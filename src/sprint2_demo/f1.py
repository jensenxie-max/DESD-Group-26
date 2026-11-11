"""Local F1 rule demonstration; no Camunda worker, provider call or persistence.

The field contract and deliberately incomplete applicability rules are recorded in
docs/sprint-2/f1-contract.json. Price bounds and field shapes are proposals for
group review, rather than additional requirements attributed to the teacher.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from .common import is_nonnegative_int, parse_date, sale_available


VERIFICATION_OUTCOMES = {None, "verified", "invalid", "unavailable"}
_TEXT_FIELDS = ("name", "description", "category", "farmOrigin")
_VALIDATION_TRACE = ["F1_Submit", "F1_Entry", "F1_Validate", "F1_Valid"]
_CORRECTION_TRACE = ["Gateway_1tq8q8b", "F1_Correction", "F1_Edit"]


def _error(field: str, code: str, message: str) -> dict:
    return {"field": field, "code": code, "message": message}


def _result(status: str, product: dict | None, errors: list[dict],
            verification_status: str, next_node: str, trace: list[str],
            pending_reason: str | None = None) -> dict:
    return {
        "status": status,
        "product": product,
        "errors": errors,
        "verificationStatus": verification_status,
        "pendingReason": pending_reason,
        "followUpRequired": pending_reason == "provider_unavailable",
        "nextNode": next_node,
        "trace": trace,
    }


def evaluate_listing(details: dict, business_date: str,
                     verification_outcome: str | None = None) -> dict:
    """Evaluate one submission or resubmission without changing caller data.

    Producer input errors return ``correction_required``. An invalid business
    date, unsupported provider outcome, or non-dict details raises ValueError:
    these are invocation errors rather than a failed producer certificate.
    ``verified`` is an injected demonstration outcome, not real verification.
    Publication and current sale availability are deliberately separate.
    """
    if not isinstance(details, dict):
        raise ValueError("details must be a dictionary")
    if (verification_outcome is not None
            and (not isinstance(verification_outcome, str)
                 or verification_outcome not in VERIFICATION_OUTCOMES)):
        raise ValueError("verification_outcome must be verified, invalid, unavailable or None")
    today = parse_date(business_date)
    errors: list[dict] = []
    product: dict[str, Any] = {"published": False, "available": False}

    for field in _TEXT_FIELDS:
        value = details.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(_error(field, "required_text", "Enter non-blank text."))
        else:
            product[field] = value.strip()

    price = details.get("price")
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        errors.append(_error("price", "invalid_price", "Enter a numeric price, excluding booleans."))
    else:
        try:
            amount = Decimal(str(price))
            if not amount.is_finite() or amount < 0:
                raise ValueError
            product["price"] = price
        except (InvalidOperation, ValueError):
            errors.append(_error("price", "invalid_price", "Proposed demo rule: price must be finite and zero or greater."))

    quantity = details.get("quantity")
    if not is_nonnegative_int(quantity):
        errors.append(_error("quantity", "invalid_quantity", "Enter a whole number of units, zero or greater, excluding booleans."))
    else:
        product["quantity"] = quantity

    dates = {}
    for field in ("startDate", "endDate"):
        try:
            dates[field] = parse_date(details.get(field))
            product[field] = dates[field].isoformat()
        except ValueError:
            errors.append(_error(field, "invalid_date", "Enter a real calendar date as YYYY-MM-DD."))
    if len(dates) == 2 and dates["endDate"] < dates["startDate"]:
        errors.append(_error("endDate", "date_order", "End date must be on or after start date."))

    claim = details.get("organicClaim", False)
    if not isinstance(claim, bool):
        errors.append(_error("organicClaim", "invalid_boolean", "Organic claim must be true or false."))
    else:
        product["organicClaim"] = claim
    reference = details.get("certificationReference")
    if claim is True and (not isinstance(reference, str) or not reference.strip()):
        errors.append(_error("certificationReference", "claim_reference_required", "Provide a reference for the claimed organic certificate."))
    elif reference is not None:
        if not isinstance(reference, str) or not reference.strip():
            errors.append(_error("certificationReference", "invalid_reference", "A supplied certificate reference must be non-blank text."))
        else:
            product["certificationReference"] = reference.strip()

    # Basic shapes only. Category-specific applicability, chronology, evidence,
    # expiry and allergen completeness are intentionally NOT implemented.
    for field in ("harvestDate", "bestBefore"):
        if field in details:
            try:
                product[field] = parse_date(details[field]).isoformat()
            except ValueError:
                errors.append(_error(field, "invalid_date", "A supplied date must use YYYY-MM-DD."))
    if "allergens" in details:
        allergens = details["allergens"]
        if (not isinstance(allergens, list)
                or any(not isinstance(item, str) or not item.strip() for item in allergens)):
            errors.append(_error("allergens", "invalid_allergens", "A supplied allergen list must contain non-blank text items."))
        else:
            product["allergens"] = [item.strip() for item in allergens]

    trace = list(_VALIDATION_TRACE)
    if errors:
        return _result("correction_required", None, errors, "not_checked", "F1_Edit",
                       trace + _CORRECTION_TRACE)

    trace.append("F1_Claim")
    if claim:
        trace.append("F1_Verify")
        if verification_outcome is None:
            return _result("verification_pending", product, [], "not_checked", "F1_Verify",
                           trace, "awaiting_verification")
        trace.append("F1_Result")
        if verification_outcome == "unavailable":
            return _result("verification_pending", product, [], "unavailable", "F1_Pending",
                           trace + ["F1_Pending", "F1_PendingNotify", "F1_PendingEnd"],
                           "provider_unavailable")
        if verification_outcome == "invalid":
            return _result("correction_required", product,
                           [_error("certificationReference", "certification_invalid", "Correct the certificate evidence or remove the unsupported claim, then resubmit.")],
                           "invalid", "F1_Edit", trace + _CORRECTION_TRACE)
        verification_status = "verified"
    else:
        verification_status = "not_required"

    product["published"] = True
    product["available"] = sale_available(product, today)
    return _result("published", product, [], verification_status, "F1_End",
                   trace + ["F1_Ready", "F1_Publish", "F1_Availability", "F1_Notify", "F1_End"])
