"""SQLite and job-contract tests. Engine integration is verified separately."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from sprint2_runtime.api import CamundaClient, CamundaError
from sprint2_runtime.business import BusinessHandlers
from sprint2_runtime.samples import listing_details, seed_product
from sprint2_runtime.store import Store
from sprint2_runtime.worker import Worker, DEFAULT_MANIFEST


DAY = "2026-11-17"


class FakeClient:
    def __init__(self):
        self.published = []
        self.failed = []
        self.completed = []
        self.jobs = []
        self.fail_completion = False

    def activate(self, kind):
        return [job for job in self.jobs if job["type"] == kind]

    def publish(self, *args):
        self.published.append(deepcopy(args))
        return {"messageKey": "123"}

    def complete(self, key, variables):
        if self.fail_completion:
            raise CamundaError(503, "unavailable")
        self.completed.append((key, deepcopy(variables)))

    def fail(self, *args):
        self.failed.append(args)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "store.sqlite3"
        self.store = Store(self.db)
        self.rules = BusinessHandlers(self.store)
        self.base = {"requestId": "request-1", "productId": "carrots", "producerId": "demo-producer", "businessDate": DAY}
        self.sequence = 0

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def action(self, name, values, key=None):
        self.sequence += 1
        return self.rules.execute(name, self.base | values, key or str(self.sequence))

    def seed(self):
        product = seed_product(DAY, "carrots")
        self.store.once("seed", "seed", lambda: (self.store.insert_product(product, "seed"), {})[1])
        return product

    def test_publication_is_persisted_and_replayed_without_duplicate_write(self):
        values = {"details": listing_details(DAY)}
        validated = self.action("F1_Validate", values)
        self.assertTrue(validated["informationValid"])
        self.assertFalse(validated["candidateProduct"]["published"])
        published = self.action("F1_Publish", values | validated, "publish-job")
        self.assertEqual(published, self.action("F1_Publish", values | validated, "publish-job"))
        self.action("F1_Availability", values | published)
        reopened = Store(self.db)
        try:
            self.assertTrue(reopened.get_product("carrots")["published"])
            self.assertEqual(1, len(reopened.snapshot()["customerAvailability"]))
        finally:
            reopened.close()

    def test_invalid_details_and_invalid_certificate_cannot_publish(self):
        invalid = {"details": listing_details(DAY) | {"name": ""}}
        result = self.action("F1_Validate", invalid)
        self.assertFalse(result["informationValid"])
        with self.assertRaises(ValueError):
            self.action("F1_Publish", invalid)
        details = listing_details(DAY) | {"organicClaim": True, "certificationReference": "DEMO-INVALID"}
        checked = self.action("F1_Verify", {"details": details})
        self.assertEqual("mock", checked["verificationMode"])
        self.assertEqual("invalid", checked["verificationStatus"])
        with self.assertRaises(ValueError):
            self.action("F1_Publish", {"details": details} | checked)
        self.assertEqual([], self.store.snapshot()["products"])

    def test_unavailable_certification_records_followup_without_listing(self):
        details = listing_details(DAY) | {"organicClaim": True, "certificationReference": "DEMO-UNAVAILABLE"}
        result = self.action("F1_Verify", {"details": details})
        self.assertEqual("unavailable", result["verificationStatus"])
        self.action("F1_Pending", result)
        state = self.store.snapshot()
        self.assertEqual([], state["products"])
        self.assertTrue(state["followUps"][0]["followUpRequired"])

    def test_retry_after_completion_failure_does_not_deduct_twice(self):
        product = self.seed()
        update = {"source": "order", "confirmed": True, "changeId": "order-1", "deduction": 3, "expectedVersion": 0}
        client = FakeClient()
        client.jobs = [{"jobKey": "100", "elementId": "F2_Save", "type": "desd.business", "retries": 3,
                        "variables": self.base | {"product": product, "update": update}, "customHeaders": {"action": "F2_Save"}}]
        client.fail_completion = True
        worker = Worker(client, self.store)
        first = worker.run_once()
        self.assertEqual(1, first["failed"])
        self.assertEqual(7, self.store.get_product("carrots")["quantity"])
        client.fail_completion = False
        second = worker.run_once()
        self.assertEqual(1, second["completed"])
        self.assertTrue(client.completed[0][1]["commitConfirmed"])
        self.assertEqual(1, self.store.get_product("carrots")["version"])
        self.assertEqual(7, self.store.get_product("carrots")["quantity"])

    def test_duplicate_order_new_job_is_not_applied(self):
        product = self.seed()
        update = {"source": "order", "confirmed": True, "changeId": "order-1", "deduction": 3, "expectedVersion": 0}
        self.action("F2_Save", {"product": product, "update": update})
        result = self.action("F2_Order", {"product": self.store.get_product("carrots"), "update": update})
        self.assertFalse(result["orderChangeApplicable"])
        self.assertEqual("duplicate", result["status"])
        self.assertEqual(7, self.store.get_product("carrots")["quantity"])

    def test_same_order_concurrent_instance_is_acknowledged_without_followup(self):
        snapshot = self.seed()
        update = {"source": "order", "confirmed": True, "changeId": "order-1", "deduction": 3, "expectedVersion": 0}
        values = {"product": snapshot, "update": update}
        self.assertTrue(self.action("F2_Order", values)["orderChangeApplicable"])
        self.assertTrue(self.action("F2_Order", values)["orderChangeApplicable"])
        self.action("F2_Save", values, "first-instance-save")
        duplicate = self.action("F2_Save", values, "second-instance-save")
        self.assertEqual("duplicate", duplicate["status"])
        self.assertTrue(duplicate["commitConfirmed"])
        self.assertFalse(duplicate["followUpRequired"])
        self.assertEqual(1, duplicate["product"]["version"])
        self.assertEqual(7, duplicate["product"]["quantity"])
        self.assertEqual([], self.store.snapshot()["followUps"])

    def test_competing_workers_cannot_commit_two_writes_for_one_version(self):
        product = self.seed()

        def commit(index):
            store = Store(self.db)
            try:
                update = {"source": "producer", "producerId": "demo-producer", "expectedVersion": 0, "quantity": 4 + index}
                return BusinessHandlers(store).execute("F2_Save", self.base | {"product": product, "update": update}, f"parallel-{index}")
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(commit, (1, 2)))
        self.assertCountEqual(["applied", "conflict"], [result["status"] for result in results])
        self.assertEqual(1, self.store.get_product("carrots")["version"])

    def test_bad_producer_change_leaves_database_unchanged(self):
        original = self.seed()
        bad = {"source": "producer", "producerId": "demo-producer", "quantity": -2, "expectedVersion": 0}
        result = self.action("F2_Producer", {"product": original, "update": bad})
        self.assertFalse(result["producerInputValid"])
        self.assertEqual(original, self.store.get_product("carrots"))
        commit = self.action("F2_Save", {"product": original, "update": bad})
        self.assertFalse(commit["commitConfirmed"])
        self.assertEqual(original, self.store.get_product("carrots"))

    def test_late_season_check_disables_customer_availability(self):
        original = self.seed()
        update = {"source": "season-check", "expectedVersion": 0}
        result = self.action("F2_Save", {"product": original, "update": update, "businessDate": "2026-12-01"})
        self.assertTrue(result["commitConfirmed"])
        self.assertFalse(result["product"]["available"])
        synced = self.action("F2_Sync", {})
        self.assertFalse(synced["customerAvailability"]["available"])
        self.assertEqual(10, result["product"]["quantity"])

    def test_message_uses_manifest_allowlist_and_request_correlation(self):
        client = FakeClient()
        worker = Worker(client, self.store)
        job = {"jobKey": "send-1", "type": "desd.message", "elementId": "F1_SendDetails",
               "customHeaders": {"action": "F1_SendDetails", "messageName": "Product details"},
               "variables": self.base | {"details": listing_details(DAY), "unrelatedPrivateValue": "omit"}}
        worker.dispatch(job)
        worker.dispatch(job)
        self.assertEqual(1, len(client.published))
        name, key, payload, message_id = client.published[0]
        self.assertEqual("Product details", name)
        self.assertEqual("request-1", key)
        self.assertEqual("send-1", message_id)
        self.assertNotIn("unrelatedPrivateValue", payload)
        self.assertEqual("request-1", payload["requestId"])

    def test_action_header_cannot_redirect_a_different_task(self):
        worker = Worker(FakeClient(), self.store)
        with self.assertRaises(ValueError):
            worker.dispatch({"jobKey": "1", "type": "desd.business", "elementId": "F1_Validate",
                             "customHeaders": {"action": "F1_Publish"}, "variables": self.base})

    def test_missing_product_is_a_visible_incident_not_a_false_outcome(self):
        client = FakeClient()
        client.jobs = [{"jobKey": "load-1", "elementId": "F2_Load", "type": "desd.business", "retries": 3,
                        "variables": self.base | {"update": {"source": "producer"}}, "customHeaders": {"action": "F2_Load"}}]
        result = Worker(client, self.store).run_once()
        self.assertEqual(1, result["failed"])
        self.assertEqual(0, client.failed[0][1])
        self.assertIn("does not exist", str(client.failed[0][2]))
        self.assertEqual([], client.published)
        self.assertEqual([], client.completed)

    def test_transient_activation_failure_recovers_but_auth_failure_is_visible(self):
        client = FakeClient()
        worker = Worker(client, self.store)
        with patch.object(client, "activate", side_effect=[CamundaError(503, "busy"), [], [], []]):
            self.assertEqual(1, worker.run_once()["activationErrors"])
            self.assertEqual(0, worker.run_once()["activationErrors"])
        with patch.object(client, "activate", side_effect=CamundaError(401, "unauthorized")):
            with self.assertRaises(CamundaError):
                worker.run_once()


class RestContractTests(unittest.TestCase):
    def test_correct_endpoint_payloads_without_network(self):
        client = CamundaClient("http://localhost:8080/v2")
        with patch.object(client, "request", return_value={"jobs": []}) as request:
            client.activate("desd.business")
            args = request.call_args.args
            self.assertEqual(("POST", "/jobs/activation"), args[:2])
            self.assertEqual(-1, args[2]["requestTimeout"])
            client.complete("123", {"ok": True})
            request.assert_called_with("POST", "/jobs/123/completion", {"variables": {"ok": True}})
            client.fail("123", 2, "error")
            self.assertEqual("/jobs/123/failure", request.call_args.args[1])
            client.publish("name", "req", {"requestId": "req"}, "123")
            self.assertEqual("/messages/publication", request.call_args.args[1])
            self.assertEqual(3600000, request.call_args.args[2]["timeToLive"])


if __name__ == "__main__":
    unittest.main()
