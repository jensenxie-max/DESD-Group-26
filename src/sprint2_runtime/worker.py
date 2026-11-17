"""Poll the two explicit BPMN job types and record real API outcomes."""

import json
import logging
from pathlib import Path
import sqlite3
import time
from urllib.error import URLError

from .api import CamundaError
from .business import BusinessHandlers, required_text


DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "models/operational/execution-manifest.json"


class Worker:
    def __init__(self, client, store, *, logger=None, manifest_path=DEFAULT_MANIFEST):
        self.client = client
        self.store = store
        self.business = BusinessHandlers(store)
        self.logger = logger or logging.getLogger("sprint2_runtime")
        self.events = []
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
        self.message_contracts = {sender: (message["name"], message["payloadFields"])
                                  for message in manifest["messages"].values() for sender in message["senders"]}

    def dispatch(self, job):
        variables = job.get("variables", {})
        headers = job.get("customHeaders", {})
        if isinstance(variables, str):
            variables = json.loads(variables)
        if isinstance(headers, str):
            headers = json.loads(headers)
        action = headers.get("action")
        if action != job.get("elementId"):
            raise ValueError("Job action must match the deployed BPMN element ID")
        operation_id = "job:" + str(job["jobKey"])
        if job["type"] == "desd.business":
            return self.business.execute(action, variables, operation_id)
        if job["type"] != "desd.message" or action not in self.message_contracts:
            raise ValueError("Unsupported job type or message action")
        name, fields = self.message_contracts[action]
        if headers.get("messageName") != name:
            raise ValueError("Message name does not match the task contract")
        request_id = required_text(variables, "requestId")
        payload = {field: variables[field] for field in fields if field in variables}
        if action in {"F1_SendDetails", "F1_ResendDetails"}:
            for field in ("productId", "producerId", "businessDate"):
                required_text(variables, field)
            if not isinstance(variables.get("details"), dict):
                raise ValueError("details must be supplied by the producer form")
        if action in {"F2_RequestContext", "F2_SubmitStockChange"}:
            required_text(variables, "producerId")
            if not isinstance(variables.get("update"), dict) or variables["update"].get("source") != "producer":
                raise ValueError("Producer message requires update.source=producer")
            payload["update"] = variables["update"] | {"producerId": variables["producerId"]}

        def publish_once():
            self.client.publish(name, request_id, payload, job["jobKey"])
            return {}

        return self.store.once(operation_id, action, publish_once)

    def run_once(self):
        counts = {"activated": 0, "completed": 0, "failed": 0, "activationErrors": 0}
        for job_type in ("desd.business", "desd.message"):
            try:
                jobs = self.client.activate(job_type)
            except CamundaError as exc:
                if exc.status not in {429, 500, 502, 503, 504}:
                    raise
                counts["activationErrors"] += 1
                self.logger.warning("activation temporarily unavailable for %s: %s", job_type, exc)
                continue
            except (URLError, OSError) as exc:
                counts["activationErrors"] += 1
                self.logger.warning("activation connection failure for %s: %s", job_type, exc)
                continue
            for job in jobs:
                counts["activated"] += 1
                try:
                    result = self.dispatch(job)
                    self.client.complete(job["jobKey"], result)
                    counts["completed"] += 1
                    event_variables = job.get("variables", {})
                    if isinstance(event_variables, str):
                        event_variables = json.loads(event_variables)
                    self.events.append({"jobKey": str(job["jobKey"]), "elementId": job["elementId"],
                                        "processInstanceKey": str(job.get("processInstanceKey", "")),
                                        "requestId": event_variables.get("requestId"), "state": "COMPLETED"})
                    self.logger.info("completed job=%s element=%s instance=%s", job["jobKey"], job["elementId"], job.get("processInstanceKey"))
                except (ValueError, KeyError, RuntimeError, URLError, OSError, sqlite3.Error) as exc:
                    counts["failed"] += 1
                    self.events.append({"jobKey": str(job["jobKey"]), "elementId": job.get("elementId"),
                                        "processInstanceKey": str(job.get("processInstanceKey", "")), "state": "FAILED", "error": str(exc)})
                    # Permanent contract errors raise an incident immediately.
                    retries = 0 if isinstance(exc, (ValueError, KeyError)) else max(0, job.get("retries", 1) - 1)
                    self.logger.error("job=%s element=%s failed: %s", job["jobKey"], job.get("elementId"), exc)
                    try:
                        self.client.fail(job["jobKey"], retries, exc)
                    except (CamundaError, URLError, OSError) as report_error:
                        self.logger.error("could not report failure for job=%s: %s", job["jobKey"], report_error)
        return counts

    def run(self, *, interval=0.5, max_cycles=None):
        cycles = 0
        backoff = interval
        while max_cycles is None or cycles < max_cycles:
            counts = self.run_once()
            backoff = min(30, max(1, backoff * 2)) if counts["activationErrors"] else interval
            cycles += 1
            if max_cycles is None or cycles < max_cycles:
                time.sleep(backoff)
