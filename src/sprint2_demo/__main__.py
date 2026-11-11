"""Run fixed, reviewable examples: python -m sprint2_demo."""

import json

from .f1 import evaluate_listing
from .f2 import evaluate_inventory_update


BUSINESS_DATE = "2026-11-12"


def examples():
    listing = {
        "name": "Carrots", "description": "Local carrots", "category": "Vegetables",
        "farmOrigin": "Demo farm", "price": 2.5, "quantity": 5,
        "startDate": "2026-11-01", "endDate": "2026-11-30", "organicClaim": False,
    }
    cases = []

    def f1(case_id, details, expected, outcome=None):
        result = evaluate_listing(details, BUSINESS_DATE, outcome)
        cases.append({"id": case_id, "input": {"details": details, "verificationOutcome": outcome, "businessDate": BUSINESS_DATE}, "expected": expected, "result": result})
        return result

    published = f1("F1-non-organic-publication", listing, {"status": "published", "published": True, "available": True})
    f1("F1-missing-name", listing | {"name": ""}, {"status": "correction_required"})
    claimed = listing | {"organicClaim": True, "certificationReference": "DEMO-CERT-1"}
    f1("F1-invalid-certificate", claimed, {"status": "correction_required", "published": False, "available": False}, "invalid")
    f1("F1-verifier-unavailable", claimed, {"status": "verification_pending", "published": False, "available": False}, "unavailable")

    # A proposed storage adapter would supply identity/version metadata. This
    # explicit in-memory enrichment is not an implemented persistence service.
    stored = published["product"] | {"productId": "demo-carrots", "producerId": "demo-producer", "version": 0, "processedChangeIds": []}

    def f2(case_id, product, update, expected, day=BUSINESS_DATE):
        result = evaluate_inventory_update(product, update, day)
        cases.append({"id": case_id, "input": {"product": product, "update": update, "businessDate": day}, "expected": expected, "result": result})
        return result

    order = {"source": "order", "expectedVersion": 0, "confirmed": True, "changeId": "demo-order-line-1", "deduction": 5}
    depleted = f2("F2-order-exhausts-stock", stored, order, {"status": "applied", "quantity": 0, "available": False})["product"]
    f2("F2-duplicate-does-not-deduct", depleted, order, {"status": "duplicate", "quantity": 0, "available": False})
    restock = {"source": "producer", "producerId": "demo-producer", "expectedVersion": 1, "quantity": 8}
    f2("F2-restock-within-period", depleted, restock, {"status": "applied", "quantity": 8, "available": True})
    f2("F2-restock-after-period", depleted, restock, {"status": "applied", "quantity": 8, "available": False}, "2026-12-01")
    f2("F2-conflict-preserves-stock", depleted, restock | {"expectedVersion": 0}, {"status": "conflict", "quantity": 0, "available": False})
    f2("F2-restock-cannot-publish", depleted | {"published": False}, restock, {"status": "applied", "quantity": 8, "published": False, "available": False})

    for case in cases:
        result = case["result"]
        product = result.get("product") or {}
        actual = {"status": result["status"], **{key: product.get(key) for key in case["expected"] if key != "status"}}
        case["matchesExpected"] = actual == case["expected"]
    return {
        "purpose": "Local business-rule examples for student review",
        "camundaExecuted": False, "realDatabaseUsed": False, "realCertificationServiceUsed": False,
        "traceMeaning": "F1 trace values reference design nodes; they are not an engine execution trace.",
        "storageAdapter": "The demo adds product identity, owner, initial version and processed IDs in memory between F1 and F2.",
        "cases": cases,
        "allExpectedResultsMatch": all(case["matchesExpected"] for case in cases),
    }


def main():
    report = examples()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["allExpectedResultsMatch"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
