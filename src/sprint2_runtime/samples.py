"""Small, explicit demo inputs; no claim that these have run in an engine."""

from calendar import monthrange
from datetime import date


def listing_details(business_date):
    day = date.fromisoformat(business_date)
    return {"name": "Local carrots", "description": "Carrots sold by the box", "category": "Vegetables",
            "farmOrigin": "Demo Bristol farm", "price": 2.5, "quantity": 10,
            "startDate": day.replace(day=1).isoformat(),
            "endDate": day.replace(day=monthrange(day.year, day.month)[1]).isoformat(),
            "organicClaim": False, "allergens": []}


def seed_product(business_date, product_id="demo-carrots", producer_id="demo-producer"):
    return listing_details(business_date) | {"productId": product_id, "producerId": producer_id,
                                           "version": 0, "processedChangeIds": [], "published": True, "available": True}
