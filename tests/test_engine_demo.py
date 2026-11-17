"""Evidence-harness checks only; these do not simulate or validate an engine."""

from copy import deepcopy
import unittest

from sprint2_runtime.demo import EngineDemo
from sprint2_runtime.samples import listing_details, seed_product
from sprint2_runtime.store import Store


DAY = "2026-11-18"


class StubClient:
    def __init__(self):
        self.requests = {}
        self.submissions = []

    def start(self, process_id, variables):
        key = str(len(self.requests) + 1)
        self.requests[key] = deepcopy(variables)
        return {"processInstanceKey": key}

    def complete_user_task(self, key, variables):
        self.submissions.append(deepcopy(variables))


class EvidenceHarness(EngineDemo):
    """Feed explicit completion observations, without network or worker jobs."""
    def __init__(self, store, *, reject_notification=True, corrupt_projection=False):
        super().__init__(StubClient(), store)
        self.reject_notification = reject_notification
        self.corrupt_projection = corrupt_projection

    def user_task(self, instance_key, element_id):
        return {"userTaskKey": instance_key, "elementId": element_id}

    def completed(self, instance_key):
        variables = self.client.requests[str(instance_key)]
        if self.reject_notification:
            self.worker.events.append({"elementId": "F2_RejectInput", "requestId": variables["requestId"]})
        if self.corrupt_projection:
            self.store.connection.execute("UPDATE customer_availability SET version=version+1")
        return {"processInstanceKey": str(instance_key), "state": "COMPLETED"}


class EvidenceHarnessTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        product = seed_product(DAY, "harness-product")
        self.store.insert_product(product, "seed")
        self.store.sync_availability(product["productId"])
        self.base = {"productId": product["productId"], "producerId": product["producerId"], "businessDate": DAY}

    def tearDown(self):
        self.store.close()

    def exercise(self, **options):
        demo = EvidenceHarness(self.store, **options)
        assertions, instances, requests = demo.invalid_inputs(self.base, "test-run", listing_details(DAY))
        return demo, assertions, instances, requests

    def test_completed_instances_without_rejection_notification_do_not_pass(self):
        _, assertions, instances, _ = self.exercise(reject_notification=False)
        self.assertEqual(3, len(instances))
        failures = [a for a in assertions if not a["passed"]]
        self.assertEqual(3, len(failures))
        self.assertTrue(all("notification" in a["check"] for a in failures))

    def test_illegal_projection_write_is_detected_even_when_instances_complete(self):
        demo, assertions, _, _ = self.exercise(corrupt_projection=True)
        failures = [a for a in assertions if not a["passed"]]
        self.assertEqual(3, len(failures))
        self.assertTrue(all("projection remains unchanged" in a["check"] for a in failures))
        self.assertEqual(0, demo.snapshots[0]["customerAvailability"]["version"])
        self.assertEqual(1, demo.snapshots[1]["customerAvailability"]["version"])

    def test_unchanged_state_with_observed_rejection_preserves_submitted_evidence(self):
        demo, assertions, _, requests = self.exercise()
        self.assertTrue(all(a["passed"] for a in assertions))
        self.assertEqual(3, len(set(requests)))
        submissions = [snapshot["submittedVariables"] for snapshot in demo.snapshots if "submittedVariables" in snapshot]
        self.assertEqual([-1, 2.5], [s["producerQuantity"] for s in submissions[:2]])
        self.assertGreater(submissions[2]["producerStartDate"], submissions[2]["producerEndDate"])


if __name__ == "__main__":
    unittest.main()
