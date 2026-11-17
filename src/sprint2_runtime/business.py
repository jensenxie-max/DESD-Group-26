"""Business handlers for the existing F1/F2 BPMN task IDs.

Certification is an explicit simulation. Producer identity and confirmed order
flags are trusted inputs to this classroom runtime, not authentication/payment
proof. Existing sprint2_demo field and inclusive sale-date rules are reused.
"""

from copy import deepcopy
import sqlite3

from sprint2_demo.common import parse_date, sale_available
from sprint2_demo.f1 import evaluate_listing
from sprint2_demo.f2 import evaluate_inventory_update


MOCK_CERTIFICATES = {"DEMO-VALID": "verified", "DEMO-INVALID": "invalid", "DEMO-UNAVAILABLE": "unavailable"}


def required_text(variables, key):
    value = variables.get(key)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{key} must be nonblank text without surrounding spaces")
    return value


class BusinessHandlers:
    def __init__(self, store):
        self.store = store

    def execute(self, action, variables, operation_id):
        required_text(variables, "requestId")
        required_text(variables, "productId")
        parse_date(variables.get("businessDate"))
        return self.store.once(operation_id, action, lambda: self._handle(action, deepcopy(variables)))

    def _listing(self, variables, outcome=None):
        return evaluate_listing(variables.get("details"), variables["businessDate"], outcome)

    def _inventory(self, variables, product=None):
        return evaluate_inventory_update(product if product is not None else variables["product"],
                                         variables.get("update"), variables["businessDate"])

    @staticmethod
    def _inventory_result(result):
        return {"status": result["status"], "validationErrors": result["errors"],
                "errors": result["errors"], "candidateProduct": result["product"]}

    def _handle(self, action, v):
        if action == "F1_Validate":
            result = self._listing(v)
            candidate = result.get("product")
            if candidate:
                candidate["published"] = False
                candidate["available"] = False
            return {"informationValid": not result["errors"], "organicClaim": v["details"].get("organicClaim") is True,
                    "validationErrors": result["errors"], "candidateProduct": candidate,
                    "verificationStatus": "not_checked", "status": "validated" if not result["errors"] else "correction_required"}
        if action == "F1_Verify":
            outcome = v.get("verificationOutcome") or MOCK_CERTIFICATES.get(v["details"].get("certificationReference"), "invalid")
            if outcome not in {"verified", "invalid", "unavailable"}:
                raise ValueError("Mock verificationOutcome must be verified, invalid or unavailable")
            result = self._listing(v, outcome)
            return {"verificationMode": "mock", "verificationStatus": outcome,
                    "validationErrors": result["errors"], "status": result["status"],
                    "pendingReason": result["pendingReason"], "followUpRequired": result["followUpRequired"]}
        if action == "F1_Publish":
            result = self._listing(v, v.get("verificationStatus") if v["details"].get("organicClaim") else None)
            if result["status"] != "published":
                raise ValueError("Publication requires validated details and any claimed certificate to be verified")
            product = result["product"] | {"productId": v["productId"], "producerId": required_text(v, "producerId"),
                                            "version": 0, "processedChangeIds": []}
            try:
                self.store.insert_product(product, v["requestId"])
            except sqlite3.IntegrityError:
                raise ValueError("productId already exists; use F2 to change existing stock, or choose a new listing ID") from None
            return {"product": product, "status": "published", "verificationStatus": result["verificationStatus"]}
        if action == "F1_Availability":
            product = self.store.get_product(v["productId"])
            return {"product": product, "customerAvailability": self.store.sync_availability(v["productId"])}
        if action == "F1_Pending":
            result = {"status": "verification_pending", "pendingReason": "provider_unavailable", "followUpRequired": True,
                      "productId": v["productId"], "verificationMode": "mock", "verificationStatus": "unavailable"}
            self.store.follow_up(v["requestId"], v["productId"], result)
            return result
        if action == "F2_Load":
            product = self.store.get_product(v["productId"])
            update = deepcopy(v.get("update", {}))
            if update.get("source") not in {"producer", "order", "season-check"}:
                raise ValueError("update.source must be producer, order or season-check")
            if update["source"] == "producer":
                producer_id = required_text(v, "producerId")
                if producer_id != product["producerId"]:
                    raise ValueError("Producer request owner does not match stored product owner")
                update["producerId"] = producer_id
            return {"product": product, "loadedVersion": product["version"], "update": update}
        if action in {"F2_Producer", "F2_Order", "F2_Season"}:
            result = self._inventory(v)
            answer = self._inventory_result(result)
            if action == "F2_Producer":
                answer["producerInputValid"] = result["status"] == "applied"
            elif action == "F2_Order":
                answer["orderChangeApplicable"] = result["status"] == "applied"
            elif result["status"] != "applied":
                # The existing season branch has no input rejection gateway.
                # Invalid integration contracts therefore become an incident.
                raise ValueError(f"Season update cannot be prepared: {result['status']}")
            return answer
        if action in {"F2_Prepare", "F2_Deduct"}:
            result = self._inventory(v)
            if result["status"] != "applied":
                raise ValueError(f"Cannot prepare a rejected change: {result['status']}")
            return self._inventory_result(result)
        if action == "F2_Assess":
            return {"saleEligible": sale_available(v["candidateProduct"], parse_date(v["businessDate"]))}
        if action in {"F2_Available", "F2_Unavailable"}:
            expected = action == "F2_Available"
            actual = sale_available(v["candidateProduct"], parse_date(v["businessDate"]))
            if actual != expected:
                raise ValueError("BPMN availability branch conflicts with the product rules")
            return {"candidateProduct": v["candidateProduct"] | {"available": actual}}
        if action == "F2_Save":
            current = self.store.get_product(v["productId"])
            result = self._inventory(v, current)
            changed = result["status"] == "applied"
            committed = result["status"] in {"applied", "duplicate"}
            if changed:
                self.store.update_product(result["product"], current["version"])
            return self._inventory_result(result) | {"product": result["product"], "commitConfirmed": committed,
                                                     "followUpRequired": not committed}
        if action == "F2_Sync":
            return {"customerAvailability": self.store.sync_availability(v["productId"])}
        if action in {"F2_Failed", "F2_RejectOrder", "F2_IntegrationResult"}:
            answer = {"status": v.get("status", "unknown"), "product": v.get("product"),
                      "errors": v.get("errors", []), "followUpRequired": action == "F2_Failed"}
            if action == "F2_Failed":
                self.store.follow_up(v["requestId"], v["productId"], answer | {"productId": v["productId"]})
            return answer
        raise ValueError(f"Unsupported business action: {action}")
