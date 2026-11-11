"""In-memory F2 business-rule prototype; not a Camunda worker or database.

The caller supplies the business date. The returned product is independent of
the inputs. A successful call simulates one versioned commit; it cannot enforce
atomicity, identity, payment confirmation or idempotency across real processes.
See docs/sprint-2/f2-contract.json for the explicit prototype assumptions.
"""

from copy import deepcopy

from .common import is_nonnegative_int, parse_date, sale_available


def _error(field, code, message):
    return {"field": field, "code": code, "message": message}


def _result(status, product, errors=()):
    return {"status": status, "product": deepcopy(product), "errors": list(errors)}


def _identifier(value):
    return isinstance(value, str) and bool(value) and value == value.strip()


def _date_range(product, prefix, errors):
    dates = {}
    for field in ("startDate", "endDate"):
        try:
            dates[field] = parse_date(product.get(field))
        except ValueError:
            errors.append(_error(prefix + field, "invalid-date", "Use a real YYYY-MM-DD date."))
    if len(dates) == 2 and dates["startDate"] > dates["endDate"]:
        errors.append(_error(prefix + "startDate", "date-order", "Start date must not exceed end date."))


def _product_errors(product):
    errors = []
    if not _identifier(product.get("producerId")):
        errors.append(_error("product.producerId", "invalid-id", "A nonblank owner ID without surrounding whitespace is required."))
    if type(product.get("published")) is not bool:
        errors.append(_error("product.published", "invalid-publication", "Published must be a boolean."))
    if not is_nonnegative_int(product.get("quantity")):
        errors.append(_error("product.quantity", "invalid-quantity", "Stored stock must be a nonnegative integer."))
    if not is_nonnegative_int(product.get("version")):
        errors.append(_error("product.version", "invalid-version", "Stored version must be a nonnegative integer."))
    ids = product.get("processedChangeIds")
    if not isinstance(ids, list) or not all(_identifier(value) for value in ids):
        errors.append(_error("product.processedChangeIds", "invalid-change-ids", "Processed IDs must be a list of nonblank strings."))
    elif len(set(ids)) != len(ids):
        errors.append(_error("product.processedChangeIds", "duplicate-stored-id", "Stored processed IDs must be unique."))
    if "available" in product and type(product["available"]) is not bool:
        errors.append(_error("product.available", "invalid-availability", "Available must be a boolean when supplied."))
    _date_range(product, "product.", errors)
    return errors


def evaluate_inventory_update(product: dict, update: dict, business_date: str) -> dict:
    """Evaluate producer, order or season-check input without mutating it.

    A malformed business_date raises ValueError (a caller/configuration error).
    Product/request business errors are returned in errors. Status is applied,
    correction-required, rejected, duplicate, conflict or invalid-product.

    producerId comparison is consistency checking of self-reported data, not
    authentication/authorization. confirmed=True is likewise a simulated
    upstream assertion, not proof that a payment or order was confirmed.
    """
    day = parse_date(business_date)
    if not isinstance(product, dict):
        return _result("invalid-product", {}, [_error("product", "invalid-product", "Product must be a dictionary.")])
    errors = _product_errors(product)
    if errors:
        return _result("invalid-product", product, errors)
    if not isinstance(update, dict):
        return _result("rejected", product, [_error("update", "invalid-update", "Update must be a dictionary.")])

    source = update.get("source")
    fields = {
        "producer": {"source", "expectedVersion", "producerId", "quantity", "startDate", "endDate"},
        "order": {"source", "expectedVersion", "confirmed", "changeId", "deduction"},
        "season-check": {"source", "expectedVersion"},
    }
    if not isinstance(source, str) or source not in fields:
        return _result("rejected", product, [_error("source", "unknown-source", "Use producer, order or season-check.")])
    invalid_status = "correction-required" if source == "producer" else "rejected"
    errors = [
        _error(str(field), "unexpected-field", "This field is not accepted for this update source.")
        for field in update if field not in fields[source]
    ]
    if not is_nonnegative_int(update.get("expectedVersion")):
        errors.append(_error("expectedVersion", "invalid-version", "Expected version must be a nonnegative integer."))

    candidate = deepcopy(product)
    if source == "producer":
        if update.get("producerId") != product["producerId"]:
            errors.append(_error("producerId", "owner-mismatch", "The self-reported producer ID does not match the stored owner."))
        changed = {"quantity", "startDate", "endDate"}.intersection(update)
        if not changed:
            errors.append(_error("update", "missing-change", "Supply quantity, startDate or endDate."))
        if "quantity" in update and not is_nonnegative_int(update["quantity"]):
            errors.append(_error("quantity", "invalid-quantity", "Producer stock is an absolute nonnegative integer."))
        for field in changed:
            candidate[field] = deepcopy(update[field])
        _date_range(candidate, "", errors)
    elif source == "order":
        if update.get("confirmed") is not True:
            errors.append(_error("confirmed", "order-not-confirmed", "Only confirmed-order updates are accepted."))
        if not _identifier(update.get("changeId")):
            errors.append(_error("changeId", "invalid-id", "A nonblank change ID without surrounding whitespace is required."))
        deduction = update.get("deduction")
        if not is_nonnegative_int(deduction) or deduction == 0:
            errors.append(_error("deduction", "invalid-deduction", "Order deduction must be a positive integer."))

    if errors:
        return _result(invalid_status, product, errors)
    # A valid retry is recognized before the optimistic version check. This is
    # deliberately in-memory: it is not a database uniqueness guarantee.
    if source == "order" and update["changeId"] in product["processedChangeIds"]:
        return _result("duplicate", product)
    if update["expectedVersion"] != product["version"]:
        return _result("conflict", product, [_error("expectedVersion", "version-conflict", "Reload the product before retrying this new change.")])
    if source == "order":
        if update["deduction"] > product["quantity"]:
            return _result("rejected", product, [_error("deduction", "insufficient-stock", "Confirmed-order deduction exceeds current stock.")])
        candidate["quantity"] -= update["deduction"]
        candidate["processedChangeIds"].append(update["changeId"])

    # Publication is inherited, never granted by an inventory change. A seasonal
    # recheck reaches this point without changing the stored stock or sale dates.
    candidate["available"] = sale_available(candidate, day)
    candidate["version"] += 1
    return _result("applied", candidate)
