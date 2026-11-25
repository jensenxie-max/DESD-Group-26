"""Week-one follow-up recovery and safe inventory-context rejection."""

from copy import deepcopy

from sprint2_runtime.business import BusinessHandlers as Sprint2Handlers, required_text


class BusinessHandlers(Sprint2Handlers):
    def _handle(self, action, v):
        request_id, product_id = v["requestId"], v["productId"]
        if action == "F1_Pending":
            current = self.store.get_follow_up(request_id)
            if current and current.get("followUpStatus") == "cancelled":
                raise ValueError("A cancelled verification request cannot be reopened; start a new listing request")
            result = {"status": "verification_pending", "pendingReason": "provider_unavailable",
                      "followUpStatus": "pending", "followUpRequired": True, "productId": product_id,
                      "verificationMode": "mock", "verificationStatus": "unavailable"}
            self.store.set_follow_up(request_id, product_id, result)
            return result
        if action == "F1_ClosePending":
            if v.get("followUpDecision") != "cancel":
                raise ValueError("Closing pending verification requires followUpDecision=cancel")
            if self.store.get_follow_up(request_id) is None:
                raise ValueError("No pending verification record exists for this request")
            notes = v.get("followUpNotes", "")
            if not isinstance(notes, str):
                raise ValueError("followUpNotes must be text")
            result = {"status": "verification_cancelled", "followUpStatus": "cancelled",
                      "followUpRequired": False, "pendingReason": "follow_up_cancelled",
                      "verificationMode": "mock", "verificationStatus": "unavailable",
                      "productId": product_id, "followUpNotes": notes[:2000]}
            self.store.set_follow_up(request_id, product_id, result)
            return result
        if action in {"F1_Verify", "F1_Publish"}:
            current = self.store.get_follow_up(request_id)
            if current and current.get("followUpStatus") == "cancelled":
                raise ValueError("A cancelled verification request cannot verify or publish")
            if action == "F1_Verify" and v.get("followUpDecision") is not None:
                if v["followUpDecision"] != "retry":
                    raise ValueError("Reverification requires followUpDecision=retry")
                if v.get("verificationOutcome") not in {"verified", "invalid", "unavailable"}:
                    raise ValueError("Select an explicit simulated provider outcome before retrying")
                if current is None:
                    raise ValueError("Reverification requires a recorded pending follow-up")
                self.store.set_follow_up(request_id, product_id,
                                         {"followUpStatus": "retrying", "followUpRequired": True,
                                          "followUpNotes": str(v.get("followUpNotes", ""))[:2000],
                                          "verificationOutcomeUsed": v["verificationOutcome"]})
            result = super()._handle(action, v)
            if action == "F1_Verify":
                # An explicit review response applies to one attempt. A later
                # corrected certificate must not inherit an old invalid result.
                outcome = result["verificationStatus"]
                result |= {"verificationOutcome": None, "followUpDecision": None,
                           "verificationAttemptOutcome": outcome}
                if current:
                    state = {"verified": "verified", "invalid": "correction_required", "unavailable": "pending"}[outcome]
                    self.store.set_follow_up(request_id, product_id,
                                             {"status": result["status"], "followUpStatus": state,
                                              "followUpRequired": True, "verificationStatus": outcome,
                                              "verificationOutcomeUsed": outcome})
            if action == "F1_Publish" and current:
                self.store.set_follow_up(request_id, product_id,
                                         {"status": "published", "followUpStatus": "resolved",
                                          "followUpRequired": False, "verificationStatus": result["verificationStatus"],
                                          "pendingReason": None})
                result |= {"followUpStatus": "resolved", "followUpRequired": False}
            return result
        if action == "F2_Load":
            update = deepcopy(v.get("update"))
            if not isinstance(update, dict) or update.get("source") not in {"producer", "order", "season-check"}:
                raise ValueError("update.source must be producer, order or season-check")
            producer_id = required_text(v, "producerId") if update["source"] == "producer" else None
            product = self.store.find_product(product_id)
            error = "product_not_found" if product is None else (
                "owner_mismatch" if producer_id is not None and producer_id != product["producerId"] else None)
            if error:
                explanation = "The requested product is unavailable." if error == "product_not_found" else "This producer cannot update the requested product."
                return {"contextAvailable": False, "contextError": error, "status": "context_rejected",
                        "errors": [{"field": "productId" if error == "product_not_found" else "producerId", "message": explanation}],
                        "product": None, "loadedVersion": None, "productId": product_id,
                        "update": {"source": update["source"]}, "followUpRequired": False}
            if producer_id is not None:
                update["producerId"] = producer_id
            return {"contextAvailable": True, "contextError": None, "status": "context_ready", "errors": [],
                    "product": product, "loadedVersion": product["version"], "update": update}
        return super()._handle(action, v)
