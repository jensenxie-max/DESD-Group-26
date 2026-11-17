"""Bounded integration exercise against a real, already deployed Camunda engine.

User tasks are completed through REST using the same form variables. This is
engine integration evidence, not a recording of manual Tasklist form usage.
"""

from datetime import datetime, timezone
import json
import time
import uuid

from .api import CamundaError
from .samples import listing_details
from .worker import Worker, DEFAULT_MANIFEST


class EngineDemo:
    def __init__(self, client, store, *, timeout=90, manifest_path=DEFAULT_MANIFEST):
        self.client = client
        self.store = store
        self.worker = Worker(client, store, manifest_path=manifest_path)
        self.timeout = timeout
        self.task_completions = []
        self.snapshots = []

    def product_snapshot(self, product_id, label, **context):
        """Keep the tested product and projection, without unrelated demo data."""
        state = self.store.snapshot()
        snapshot = {
            "label": label,
            "product": next((p for p in state["products"] if p["productId"] == product_id), None),
            "customerAvailability": next((p for p in state["customerAvailability"] if p["product_id"] == product_id), None),
            "followUps": [p for p in state["followUps"] if p.get("productId") == product_id],
            **context,
        }
        self.snapshots.append(snapshot)
        return snapshot

    def business_results(self, request_ids):
        """Attach persisted handler outcomes to their observed real job keys."""
        results = []
        for event in self.worker.events:
            if event.get("requestId") not in request_ids or event.get("state") != "COMPLETED":
                continue
            row = self.store.connection.execute(
                "SELECT action,result FROM operations WHERE operation_id=?",
                ("job:" + event["jobKey"],),
            ).fetchone()
            if row is not None and event["elementId"] in {
                "F1_Validate", "F1_Verify", "F1_Pending", "F2_Producer", "F2_Order",
                "F2_Season", "F2_Save", "F2_Failed", "F2_RejectOrder",
            }:
                results.append(event | {"result": json.loads(row["result"])})
        return results

    def wait_for(self, description, check):
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            counts = self.worker.run_once()
            if counts["failed"]:
                raise RuntimeError(f"Worker reported a failed job while waiting for {description}; inspect the engine incident and worker log")
            try:
                result = check()
                if result:
                    return result
            except CamundaError as exc:
                # Newly started instances are absent from the search index briefly.
                if exc.status != 404:
                    raise
            time.sleep(0.3)
        raise TimeoutError(f"Timed out waiting for {description}; inspect Tasklist/Operate, do not assume success")

    def user_task(self, instance_key, element_id):
        def find():
            response = self.client.request("POST", "/user-tasks/search", {
                "filter": {"processInstanceKey": str(instance_key), "state": "CREATED"}})
            return next((item for item in response.get("items", []) if item["elementId"] == element_id), None)
        return self.wait_for(f"{element_id} in instance {instance_key}", find)

    def complete_task(self, task, variables):
        self.client.complete_user_task(task["userTaskKey"], variables)
        self.task_completions.append({"userTaskKey": str(task["userTaskKey"]), "elementId": task["elementId"],
                                      "method": "REST user-task completion", "variables": variables})

    def completed(self, instance_key):
        def check():
            instance = self.client.request("GET", f"/process-instances/{instance_key}")
            if instance.get("hasIncident"):
                raise RuntimeError(f"Instance {instance_key} has an incident")
            return instance if instance.get("state", "").upper() == "COMPLETED" else None
        return self.wait_for(f"completed instance {instance_key}", check)

    def integration_request(self, base, request_id, update):
        self.client.publish("F2 update request", request_id, base | {"requestId": request_id, "update": update}, "request:" + request_id)

        def find_instance():
            return next((event["processInstanceKey"] for event in self.worker.events
                         if event.get("requestId") == request_id), None)
        key = self.wait_for(f"platform instance for {request_id}", find_instance)
        return self.completed(key)

    def boundaries(self, base, run_id, details):
        """Exercise actual order/duplicate/commit-conflict/season BPMN paths."""
        assertions, instances, requests = [], [], []
        product_id = base["productId"]
        current = self.store.get_product(product_id)
        self.product_snapshot(product_id, "before order exhaustion")
        change_id = "order-" + run_id
        order = {"source": "order", "expectedVersion": current["version"], "confirmed": True,
                 "changeId": change_id, "deduction": current["quantity"]}
        request_id = "order-" + run_id
        requests.append(request_id)
        instances.append(self.integration_request(base, request_id, order))
        depleted = self.store.get_product(product_id)
        self.product_snapshot(product_id, "after order exhaustion", requestId=request_id)
        assertions.append({"check": "actual order path exhausts stock and disables sale", "passed": depleted["quantity"] == 0 and not depleted["available"]})
        request_id = "duplicate-" + run_id
        requests.append(request_id)
        instances.append(self.integration_request(base, request_id, order))
        self.product_snapshot(product_id, "after duplicate order", requestId=request_id)
        assertions.append({"check": "actual duplicate order path preserves stock and version", "passed": self.store.get_product(product_id) == depleted})

        request_id = "conflict-" + run_id
        requests.append(request_id)
        started = self.client.start("F2_ProducerProcess", base | {"requestId": request_id, "update": {"source": "producer", "producerId": base["producerId"]}})
        task = self.user_task(started["processInstanceKey"], "F2_EnterStockChange")
        concurrent_id = "concurrent-" + run_id
        requests.append(concurrent_id)
        instances.append(self.integration_request(base, concurrent_id, {"source": "season-check", "expectedVersion": depleted["version"]}))
        concurrent = self.store.get_product(product_id)
        self.product_snapshot(product_id, "after concurrent seasonal commit", requestId=concurrent_id)
        self.complete_task(task, {"producerQuantity": 9, "producerStartDate": details["startDate"], "producerEndDate": details["endDate"]})
        instances.append(self.completed(started["processInstanceKey"]))
        self.product_snapshot(product_id, "after rejected stale-version commit", requestId=request_id)
        assertions.append({"check": "actual stale-version commit does not overwrite a concurrent change", "passed": self.store.get_product(product_id) == concurrent})
        follow_up = self.store.connection.execute("SELECT body FROM follow_ups WHERE request_id=?", (request_id,)).fetchone()
        assertions.append({"check": "actual commit conflict records a follow-up", "passed": follow_up is not None})

        request_id = "restock-" + run_id
        requests.append(request_id)
        started = self.client.start("F2_ProducerProcess", base | {"requestId": request_id, "update": {"source": "producer", "producerId": base["producerId"]}})
        task = self.user_task(started["processInstanceKey"], "F2_EnterStockChange")
        self.complete_task(task, {"producerQuantity": 8, "producerStartDate": details["startDate"], "producerEndDate": details["endDate"]})
        instances.append(self.completed(started["processInstanceKey"]))
        restocked = self.store.get_product(product_id)
        self.product_snapshot(product_id, "after producer restock", requestId=request_id)
        assertions.append({"check": "actual producer restock restores availability within sale dates", "passed": restocked["quantity"] == 8 and restocked["available"]})
        from datetime import date, timedelta
        outside_date = (date.fromisoformat(details["endDate"]) + timedelta(days=1)).isoformat()
        request_id = "outside-season-" + run_id
        requests.append(request_id)
        instances.append(self.integration_request(base | {"businessDate": outside_date}, request_id,
                                                   {"source": "season-check", "expectedVersion": restocked["version"]}))
        outside = self.store.get_product(product_id)
        self.product_snapshot(product_id, "after out-of-season check", requestId=request_id, businessDate=outside_date)
        assertions.append({"check": "actual out-of-season path keeps positive stock but disables sale", "passed": outside["quantity"] == 8 and not outside["available"]})
        return assertions, instances, requests

    def invalid_inputs(self, base, run_id, details):
        """Bypass browser validation to test the real server rejection branch."""
        assertions, instances, requests = [], [], []
        valid_values = {"producerQuantity": 6, "producerStartDate": details["startDate"],
                        "producerEndDate": details["endDate"]}
        cases = (
            ("negative-stock", {"producerQuantity": -1}),
            ("fractional-stock", {"producerQuantity": 2.5}),
            ("reversed-dates", {"producerStartDate": details["endDate"], "producerEndDate": details["startDate"]}),
        )
        for name, invalid_values in cases:
            request_id = name + "-" + run_id
            requests.append(request_id)
            before = self.product_snapshot(base["productId"], "before " + name, requestId=request_id)
            started = self.client.start("F2_ProducerProcess", base | {
                "requestId": request_id, "update": {"source": "producer", "producerId": base["producerId"]}})
            task = self.user_task(started["processInstanceKey"], "F2_EnterStockChange")
            submitted = valid_values | invalid_values
            self.complete_task(task, submitted)
            instances.append(self.completed(started["processInstanceKey"]))
            after = self.product_snapshot(base["productId"], "after " + name,
                                          requestId=request_id, submittedVariables=submitted)
            actions = {event["elementId"] for event in self.worker.events if event.get("requestId") == request_id}
            assertions.extend([
                {"check": name + ": real rejection notification completes", "passed": "F2_RejectInput" in actions},
                {"check": name + ": product including version remains unchanged", "passed": after["product"] == before["product"]},
                {"check": name + ": customer projection remains unchanged", "passed": after["customerAvailability"] == before["customerAvailability"]},
                {"check": name + ": rejected input never reaches commit or projection sync", "passed": not {"F2_Save", "F2_Sync"}.intersection(actions)},
            ])
        return assertions, instances, requests

    def run(self, business_date, scenario="happy"):
        run_id = str(uuid.uuid4())
        product_id = "demo-" + run_id
        producer_id = "demo-producer"
        details = listing_details(business_date)
        if scenario in {"organic", "pending", "invalid-certificate"}:
            reference = {"organic": "DEMO-VALID", "pending": "DEMO-UNAVAILABLE", "invalid-certificate": "DEMO-INVALID"}[scenario]
            details |= {"organicClaim": True, "certificationReference": reference}
        assertions = []
        base = {"productId": product_id, "producerId": producer_id, "businessDate": business_date}
        f1_request = "f1-" + run_id
        started_f1 = self.client.start("F1_ProducerProcess", base | {"requestId": f1_request, "details": details})
        f1_key = str(started_f1["processInstanceKey"])
        task = self.user_task(f1_key, "F1_Submit")
        submitted = details | ({"name": ""} if scenario == "correction" else {})
        self.complete_task(task, {"details": submitted, "allergenEntries": []})
        if scenario in {"correction", "invalid-certificate"}:
            correction = self.user_task(f1_key, "F1_Edit")
            rejected = self.product_snapshot(product_id, "waiting for F1 correction",
                                             requestId=f1_request, correctionTaskKey=str(correction["userTaskKey"]),
                                             submittedDetails=submitted)
            assertions.append({"check": "F1 correction user task exists before resubmission", "passed": correction["elementId"] == "F1_Edit"})
            assertions.append({"check": "rejected F1 details have no published product or customer projection",
                               "passed": rejected["product"] is None and rejected["customerAvailability"] is None})
            if scenario == "invalid-certificate":
                details = details | {"certificationReference": "DEMO-VALID"}
            self.complete_task(correction, {"details": details, "allergenEntries": []})
        producer_instances = [self.completed(f1_key)]
        boundary_instances, boundary_requests = [], []
        self.product_snapshot(product_id, "after F1 outcome", requestId=f1_request)
        if scenario == "pending":
            state = self.store.snapshot()
            assertions.append({"check": "unavailable mock certificate does not publish", "passed": not any(p["productId"] == product_id for p in state["products"])})
            assertions.append({"check": "follow-up is persisted", "passed": any(f["productId"] == product_id for f in state["followUps"])})
        else:
            before = self.store.get_product(product_id)
            assertions.append({"check": "F1 published persisted listing", "passed": before["published"] and before["quantity"] == 10})
            if scenario in {"correction", "invalid-certificate"}:
                f1_actions = [e["elementId"] for e in self.worker.events if e.get("requestId") == f1_request]
                assertions.append({"check": "F1 sent correction, received resubmission and revalidated",
                                   "passed": "F1_Correction" in f1_actions and "F1_ResendDetails" in f1_actions and f1_actions.count("F1_Validate") == 2})
                if scenario == "invalid-certificate":
                    assertions.append({"check": "invalid mock certificate was reverified after correction",
                                       "passed": f1_actions.count("F1_Verify") == 2 and before.get("certificationReference") == "DEMO-VALID"})
            f2_request = "f2-" + run_id
            started_f2 = self.client.start("F2_ProducerProcess", base | {"requestId": f2_request, "update": {"source": "producer", "producerId": producer_id}})
            f2_key = str(started_f2["processInstanceKey"])
            stock_task = self.user_task(f2_key, "F2_EnterStockChange")
            self.complete_task(stock_task, {"producerQuantity": 6, "producerStartDate": details["startDate"], "producerEndDate": details["endDate"]})
            producer_instances.append(self.completed(f2_key))
            after = self.store.get_product(product_id)
            self.product_snapshot(product_id, "after valid F2 stock update", requestId=f2_request)
            assertions.append({"check": "F2 changed stock and incremented version once", "passed": after["quantity"] == 6 and after["version"] == 1})
            projection = next((r for r in self.store.snapshot()["customerAvailability"] if r["product_id"] == product_id), None)
            assertions.append({"check": "customer availability projection matches latest version", "passed": projection is not None and projection["version"] == 1 and bool(projection["available"]) == after["available"]})
            if scenario == "boundaries":
                more, boundary_instances, boundary_requests = self.boundaries(base, run_id, details)
                assertions.extend(more)
            elif scenario == "invalid-input":
                more, invalid_instances, boundary_requests = self.invalid_inputs(base, run_id, details)
                producer_instances.extend(invalid_instances)
                assertions.extend(more)
        request_ids = {"f1-" + run_id, "f2-" + run_id, *boundary_requests}
        events = [event for event in self.worker.events if event.get("requestId") in request_ids]
        platform_keys = sorted({e["processInstanceKey"] for e in events} - {str(i["processInstanceKey"]) for i in producer_instances + boundary_instances})
        platform_instances = [self.completed(key) for key in platform_keys]
        passed = all(assertion["passed"] for assertion in assertions)
        if not passed:
            raise AssertionError(f"Actual engine demo assertions failed: {assertions}")
        return {"runId": run_id, "scenario": scenario, "recordedAt": datetime.now(timezone.utc).isoformat(),
                "businessDate": business_date, "productId": product_id, "engineExecuted": True,
                "certificationMode": "mock fixtures; no external certification provider contacted",
                "formInteraction": "Automated REST completion of actual Camunda user tasks",
                "producerInstances": producer_instances, "platformInstances": platform_instances,
                "boundaryInstances": boundary_instances,
                "stateSnapshots": self.snapshots,
                "taskCompletions": self.task_completions, "completedJobs": events,
                "businessResults": self.business_results(request_ids),
                "assertions": assertions, "allAssertionsPassed": passed}
