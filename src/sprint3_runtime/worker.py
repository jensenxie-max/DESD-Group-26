"""Isolated Sprint 3 workers and transport observations for safe operator recovery."""

import json
import logging
from pathlib import Path
import sqlite3
from urllib.error import URLError

from sprint2_runtime.api import CamundaError
from sprint2_runtime.business import required_text
from sprint2_runtime.worker import Worker as Sprint2Worker

from .business import BusinessHandlers


DEFAULT_MANIFEST = Path(__file__).resolve().parents[2] / "models/sprint3/execution-manifest.json"
BUSINESS_JOB_TYPE = "desd.s3.business"
MESSAGE_JOB_TYPE = "desd.s3.message"


class DeliveryUncertain(ValueError):
    """A recipient may have received the message; verification is required before retry."""


class Worker(Sprint2Worker):
    def __init__(self, client, store, *, logger=None, manifest_path=DEFAULT_MANIFEST):
        super().__init__(client, store, logger=logger or logging.getLogger("sprint3_runtime"), manifest_path=manifest_path)
        self.business = BusinessHandlers(store)

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
        if job["type"] == BUSINESS_JOB_TYPE:
            return self.business.execute(action, variables, operation_id)
        if job["type"] != MESSAGE_JOB_TYPE or action not in self.message_contracts:
            raise ValueError("Unsupported Sprint 3 job type or message action")
        name, fields = self.message_contracts[action]
        if not name.startswith("S3 ") or headers.get("messageName") != name:
            raise ValueError("Message name does not match the isolated Sprint 3 contract")
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
        if action == "F2_RejectContext":
            if variables.get("contextAvailable") is not False:
                raise ValueError("Context rejection requires contextAvailable=false")
            # A supplied/old product value must never leak into an ownership rejection.
            payload["product"] = None
            payload["loadedVersion"] = None
            payload["update"] = {"source": variables.get("update", {}).get("source")}

        record = self.store.prepare_message(operation_id, action, name, request_id, job["jobKey"], payload)
        if record["status"] == "accepted":
            return {}
        if record["status"] != "prepared" or not self.store.claim_message(operation_id):
            raise DeliveryUncertain("Outbox delivery is uncertain; inspect the receiving instance and reconcile the recorded operation before resolving the incident")
        try:
            response = self.client.publish(name, request_id, payload, job["jobKey"])
            self.store.message_accepted(operation_id, response)
        except (CamundaError, URLError, OSError, sqlite3.Error) as exc:
            # Transport errors do not prove that the broker failed to accept the message.
            self.store.message_uncertain(operation_id, exc)
            raise DeliveryUncertain("Message delivery needs operator verification; see the outbox record. " + str(exc)) from exc
        return {}

    def run_once(self):
        counts = {"activated": 0, "completed": 0, "failed": 0, "activationErrors": 0}
        for job_type in (BUSINESS_JOB_TYPE, MESSAGE_JOB_TYPE):
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
                    variables = job.get("variables", {})
                    if isinstance(variables, str):
                        variables = json.loads(variables)
                    self.events.append({"jobKey": str(job["jobKey"]), "elementId": job["elementId"],
                                        "processInstanceKey": str(job.get("processInstanceKey", "")),
                                        "requestId": variables.get("requestId"), "state": "COMPLETED"})
                    self.logger.info("completed job=%s element=%s instance=%s", job["jobKey"], job["elementId"], job.get("processInstanceKey"))
                except (ValueError, KeyError, RuntimeError, URLError, OSError, sqlite3.Error) as exc:
                    counts["failed"] += 1
                    self.events.append({"jobKey": str(job["jobKey"]), "elementId": job.get("elementId"),
                                        "processInstanceKey": str(job.get("processInstanceKey", "")), "state": "FAILED", "error": str(exc)})
                    retries = 0 if isinstance(exc, (ValueError, KeyError)) else max(0, job.get("retries", 1) - 1)
                    self.logger.error("job=%s element=%s failed: %s", job["jobKey"], job.get("elementId"), exc)
                    try:
                        self.client.fail(job["jobKey"], retries, exc)
                    except (CamundaError, URLError, OSError) as report_error:
                        self.logger.error("could not report failure for job=%s: %s", job["jobKey"], report_error)
        return counts
