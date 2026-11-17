"""F2 boundary, retry and state-preservation examples for the local prototype."""

from copy import deepcopy
import unittest

from sprint2_demo.f2 import evaluate_inventory_update


class InventoryUpdateTests(unittest.TestCase):
    def setUp(self):
        self.product = {
            "productId": "apples-1", "producerId": "farm-1", "published": True,
            "quantity": 10, "startDate": "2026-11-01", "endDate": "2026-11-30",
            "available": True, "version": 3, "processedChangeIds": [],
            "metadata": {"unit": "box"},
        }

    def producer(self, **changes):
        return {"source": "producer", "producerId": "farm-1", "expectedVersion": 3, **changes}

    def order(self, **changes):
        return {"source": "order", "confirmed": True, "changeId": "order-7-line-1",
                "deduction": 4, "expectedVersion": 3, **changes}

    def evaluate(self, update, day="2026-11-11", product=None):
        return evaluate_inventory_update(self.product if product is None else product, update, day)

    def assert_unchanged(self, update, status, code=None, product=None):
        original = deepcopy(self.product if product is None else product)
        original_update = deepcopy(update)
        result = self.evaluate(update, product=original)
        self.assertEqual(status, result["status"])
        self.assertEqual(self.product if product is None else product, result["product"])
        self.assertEqual(original_update, update)
        if code:
            self.assertIn(code, [error["code"] for error in result["errors"]])
        return result

    def test_producer_value_replaces_stock_and_keeps_publication(self):
        result = self.evaluate(self.producer(quantity=4))
        self.assertEqual("applied", result["status"])
        self.assertEqual(4, result["product"]["quantity"])
        self.assertEqual(4, result["product"]["version"])
        self.assertTrue(result["product"]["published"])
        self.assertTrue(result["product"]["available"])
        self.assertEqual([], result["product"]["processedChangeIds"])

    def test_zero_stock_and_restock_outside_season_stay_unavailable(self):
        zero = self.evaluate(self.producer(quantity=0))["product"]
        self.assertFalse(zero["available"])
        restock = evaluate_inventory_update(zero, self.producer(quantity=5, expectedVersion=4), "2026-12-01")
        self.assertEqual(5, restock["product"]["quantity"])
        self.assertFalse(restock["product"]["available"])

    def test_restock_cannot_publish_an_unapproved_product(self):
        self.product["published"] = False
        result = self.evaluate(self.producer(quantity=5))
        self.assertFalse(result["product"]["published"])
        self.assertFalse(result["product"]["available"])

    def test_restock_within_season_reopens_an_approved_product(self):
        self.product["quantity"] = 0
        self.product["available"] = False
        result = self.evaluate(self.producer(quantity=5))
        self.assertEqual("applied", result["status"])
        self.assertEqual(5, result["product"]["quantity"])
        self.assertTrue(result["product"]["available"])

    def test_date_only_update_can_close_the_season(self):
        result = self.evaluate(self.producer(endDate="2026-11-10"))
        self.assertEqual("applied", result["status"])
        self.assertEqual(10, result["product"]["quantity"])
        self.assertFalse(result["product"]["available"])

    def test_season_recheck_preserves_quantity_and_includes_both_boundaries(self):
        update = {"source": "season-check", "expectedVersion": 3}
        for day, available in [("2026-10-31", False), ("2026-11-01", True),
                               ("2026-11-30", True), ("2026-12-01", False)]:
            with self.subTest(day=day):
                result = self.evaluate(update, day)
                self.assertEqual("applied", result["status"])
                self.assertEqual(10, result["product"]["quantity"])
                self.assertEqual(available, result["product"]["available"])
                self.assertEqual(self.product["startDate"], result["product"]["startDate"])
                self.assertEqual(self.product["endDate"], result["product"]["endDate"])

    def test_bad_business_date_is_a_caller_error(self):
        for day in ["2026-1-01", "2026-02-29", "2026-11-11T00:00:00Z", None]:
            with self.subTest(day=day), self.assertRaises(ValueError):
                self.evaluate(self.producer(quantity=5), day)

    def test_bad_producer_quantities_are_not_coerced(self):
        for value in [-1, 1.5, True, "4", None]:
            with self.subTest(value=value):
                self.assert_unchanged(self.producer(quantity=value), "correction-required", "invalid-quantity")

    def test_reversed_or_malformed_producer_dates_require_correction(self):
        for fields, code in [({"startDate": "2026-12-01"}, "date-order"),
                             ({"startDate": "2026-1-02"}, "invalid-date"),
                             ({"endDate": "2026-02-29"}, "invalid-date")]:
            with self.subTest(fields=fields):
                self.assert_unchanged(self.producer(**fields), "correction-required", code)

    def test_owner_mismatch_and_publication_overwrite_do_not_change_product(self):
        self.assert_unchanged(self.producer(quantity=8, producerId="another-farm"), "correction-required", "owner-mismatch")
        self.assert_unchanged(self.producer(quantity=8, published=True), "correction-required", "unexpected-field")

    def test_order_exactly_exhausts_stock_and_records_change_once(self):
        result = self.evaluate(self.order(deduction=10))
        self.assertEqual("applied", result["status"])
        self.assertEqual(0, result["product"]["quantity"])
        self.assertFalse(result["product"]["available"])
        self.assertEqual(["order-7-line-1"], result["product"]["processedChangeIds"])
        self.assertEqual(4, result["product"]["version"])

    def test_replaying_an_applied_order_with_old_version_does_not_deduct_twice(self):
        update = self.order()
        first = self.evaluate(update)
        second = self.evaluate(update, product=first["product"])
        self.assertEqual("duplicate", second["status"])
        self.assertEqual(first["product"], second["product"])
        self.assertEqual(6, second["product"]["quantity"])
        self.assertEqual([], second["errors"])

    def test_insufficient_stock_does_not_record_an_order_as_processed(self):
        result = self.assert_unchanged(self.order(deduction=11), "rejected", "insufficient-stock")
        self.assertEqual([], result["product"]["processedChangeIds"])

    def test_orders_require_confirmed_flag_positive_integer_and_change_id(self):
        for update, code in [(self.order(confirmed=False), "order-not-confirmed"),
                             (self.order(confirmed=1), "order-not-confirmed"),
                             (self.order(changeId=" "), "invalid-id")]:
            with self.subTest(update=update):
                self.assert_unchanged(update, "rejected", code)
        for value in [0, -1, True, 2.5, "2"]:
            with self.subTest(deduction=value):
                self.assert_unchanged(self.order(deduction=value), "rejected", "invalid-deduction")

    def test_each_new_source_requires_the_current_version(self):
        for update in [self.producer(quantity=5, expectedVersion=2), self.order(expectedVersion=2),
                       {"source": "season-check", "expectedVersion": 2}]:
            with self.subTest(source=update["source"]):
                self.assert_unchanged(update, "conflict", "version-conflict")

    def test_invalid_stored_stock_or_tracking_is_not_repaired_silently(self):
        for field, value in [("quantity", True), ("quantity", -1), ("version", "3"),
                             ("processedChangeIds", ["same", "same"]), ("startDate", "2026-12-01")]:
            with self.subTest(field=field, value=value):
                invalid = deepcopy(self.product)
                invalid[field] = value
                self.assert_unchanged(self.producer(quantity=5), "invalid-product", product=invalid)

    def test_results_and_inputs_do_not_share_mutable_product_state(self):
        for update in [self.producer(quantity=5), self.order(expectedVersion=2)]:
            with self.subTest(update=update):
                before_product, before_update = deepcopy(self.product), deepcopy(update)
                result = self.evaluate(update)
                self.assertEqual(before_product, self.product)
                self.assertEqual(before_update, update)
                result["product"]["metadata"]["unit"] = "changed"
                result["product"]["processedChangeIds"].append("external-mutation")
                self.assertEqual(before_product, self.product)

    def test_unknown_sources_and_mutating_season_payload_are_rejected(self):
        self.assert_unchanged({"source": "payment", "expectedVersion": 3}, "rejected", "unknown-source")
        self.assert_unchanged({"source": "season-check", "expectedVersion": 3, "quantity": 0}, "rejected", "unexpected-field")


if __name__ == "__main__":
    unittest.main()
