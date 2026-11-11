"""Shared proposed availability rule, based on the existing F1/F2 task notes."""

from datetime import date, datetime
import re


def parse_date(value: str) -> date:
    """Accept a calendar-valid YYYY-MM-DD string without coercion."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValueError("Date must be a YYYY-MM-DD string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Date must be a valid calendar date") from exc


def is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def sale_available(product: dict, business_date: date) -> bool:
    """Calculate a result; no persistence, authentication or clock is provided.

    Inclusive date boundaries and integer stock units are prototype assumptions.
    Callers supply the business date explicitly; timezone policy is unresolved.
    """
    if not isinstance(business_date, date) or isinstance(business_date, datetime):
        raise ValueError("business_date must be a date")
    if not isinstance(product.get("published"), bool):
        raise ValueError("published must be a boolean")
    if not is_nonnegative_int(product.get("quantity")):
        raise ValueError("quantity must be a nonnegative integer")
    start = parse_date(product.get("startDate"))
    end = parse_date(product.get("endDate"))
    if start > end:
        raise ValueError("startDate must not follow endDate")
    return product["published"] and product["quantity"] > 0 and start <= business_date <= end
