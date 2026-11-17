"""Business-path checks for the local F1 prototype, not deployed-engine tests."""

import copy
import unittest

from sprint2_demo.f1 import evaluate_listing


def valid_details(**changes):
    details = {
        "name": "Carrots", "description": "Fresh local carrots", "category": "Vegetables",
        "price": 2.50, "quantity": 12, "startDate": "2026-11-01", "endDate": "2026-11-30",
        "farmOrigin": "Bristol Farm", "organicClaim": False,
    }
    details.update(changes)
    return details


class F1ListingTests(unittest.TestCase):
    business_date = "2026-11-12"

    def evaluate(self, details=None, outcome=None, business_date=None):
        return evaluate_listing(valid_details() if details is None else details,
                                business_date or self.business_date, outcome)

    def assert_correction(self, result, field):
        self.assertEqual(result["status"], "correction_required")
        self.assertIn(field, {error["field"] for error in result["errors"]})
        self.assertTrue(result["product"] is None or not result["product"]["published"])
        self.assertEqual(result["nextNode"], "F1_Edit")

    def test_non_organic_listing_publishes_without_provider(self):
        result = self.evaluate()
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["verificationStatus"], "not_required")
        self.assertTrue(result["product"]["available"])
        self.assertNotIn("F1_Verify", result["trace"])
        self.assertEqual(result["errors"], [])

    def test_missing_required_fields_return_field_errors(self):
        for field in ("name", "description", "category", "farmOrigin", "price", "quantity", "startDate", "endDate"):
            with self.subTest(field=field):
                details = valid_details()
                del details[field]
                self.assert_correction(self.evaluate(details), field)

    def test_text_must_be_non_blank(self):
        for value in ("   ", None, False, 123):
            with self.subTest(value=value):
                self.assert_correction(self.evaluate(valid_details(name=value)), "name")

    def test_negative_fractional_and_boolean_quantity_are_rejected(self):
        for value in (-1, 1.5, True, False, "3"):
            with self.subTest(value=value):
                self.assert_correction(self.evaluate(valid_details(quantity=value)), "quantity")

    def test_zero_stock_publishes_but_is_not_available(self):
        result = self.evaluate(valid_details(quantity=0))
        self.assertEqual(result["status"], "published")
        self.assertTrue(result["product"]["published"])
        self.assertFalse(result["product"]["available"])

    def test_strict_real_dates(self):
        for field in ("startDate", "endDate"):
            for value in ("2026-2-01", "2026-02-29", "2026-11-01T00:00:00", "20261101", None, False):
                with self.subTest(field=field, value=value):
                    self.assert_correction(self.evaluate(valid_details(**{field: value})), field)

    def test_reversed_selling_dates_require_correction(self):
        self.assert_correction(self.evaluate(valid_details(startDate="2026-12-01")), "endDate")

    def test_sale_window_uses_inclusive_dates(self):
        for business_date, available in (("2026-10-31", False), ("2026-11-01", True),
                                         ("2026-11-30", True), ("2026-12-01", False)):
            with self.subTest(business_date=business_date):
                result = self.evaluate(business_date=business_date)
                self.assertEqual(result["status"], "published")
                self.assertEqual(result["product"]["available"], available)

    def test_proposed_price_shape_and_nonnegative_finite_rule(self):
        for value in (True, False, "2.50", -1, float("nan"), float("inf")):
            with self.subTest(value=value):
                self.assert_correction(self.evaluate(valid_details(price=value)), "price")
        for value in (0, 0.01, 100000.01, 2.001):
            with self.subTest(allowed=value):
                self.assertEqual(self.evaluate(valid_details(price=value))["status"], "published")

    def test_organic_claim_must_be_boolean(self):
        for value in ("true", 1, 0, None):
            with self.subTest(value=value):
                self.assert_correction(self.evaluate(valid_details(organicClaim=value)), "organicClaim")

    def test_claim_needs_reference_before_provider_result_can_publish(self):
        self.assert_correction(self.evaluate(valid_details(organicClaim=True), "verified"), "certificationReference")

    def test_verified_organic_claim_publishes(self):
        result = self.evaluate(valid_details(organicClaim=True, certificationReference="DEMO-CERT-1"), "verified")
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["verificationStatus"], "verified")
        self.assertTrue(result["product"]["published"])

    def test_invalid_certificate_enters_correction_path(self):
        result = self.evaluate(valid_details(organicClaim=True, certificationReference="DEMO-CERT-1"), "invalid")
        self.assert_correction(result, "certificationReference")
        self.assertEqual(result["verificationStatus"], "invalid")
        self.assertFalse(result["followUpRequired"])

    def test_provider_outage_stays_unpublished_without_invalid_certificate_error(self):
        result = self.evaluate(valid_details(organicClaim=True, certificationReference="DEMO-CERT-1"), "unavailable")
        self.assertEqual(result["status"], "verification_pending")
        self.assertEqual(result["verificationStatus"], "unavailable")
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["followUpRequired"])
        self.assertFalse(result["product"]["published"])
        self.assertFalse(result["product"]["available"])
        self.assertEqual(result["nextNode"], "F1_Pending")

    def test_missing_provider_result_waits_without_publication(self):
        result = self.evaluate(valid_details(organicClaim=True, certificationReference="DEMO-CERT-1"))
        self.assertEqual(result["status"], "verification_pending")
        self.assertEqual(result["pendingReason"], "awaiting_verification")
        self.assertFalse(result["product"]["published"])
        self.assertEqual(result["nextNode"], "F1_Verify")

    def test_optional_information_checks_format_only(self):
        self.assert_correction(self.evaluate(valid_details(harvestDate="2026-11-99")), "harvestDate")
        self.assert_correction(self.evaluate(valid_details(bestBefore="11/30/2026")), "bestBefore")
        self.assert_correction(self.evaluate(valid_details(allergens="nuts")), "allergens")
        result = self.evaluate(valid_details(harvestDate="2026-11-01", bestBefore="2026-11-30", allergens=["celery"]))
        self.assertEqual(result["status"], "published")

    def test_input_is_not_mutated_and_resubmission_is_revalidated(self):
        details = valid_details(quantity=-1, allergens=[" celery "])
        original = copy.deepcopy(details)
        self.assertEqual(self.evaluate(details)["status"], "correction_required")
        self.assertEqual(details, original)
        details["quantity"] = 5
        result = self.evaluate(details)
        self.assertEqual(result["status"], "published")
        self.assertEqual(details["allergens"], [" celery "])
        self.assertEqual(result["product"]["allergens"], ["celery"])

    def test_invalid_invocation_is_not_a_producer_certificate_failure(self):
        for outcome in ("timeout", "success", True, []):
            with self.subTest(outcome=outcome):
                with self.assertRaises(ValueError):
                    self.evaluate(outcome=outcome)
        with self.assertRaises(ValueError):
            self.evaluate(business_date="2026-11-99")
        with self.assertRaises(ValueError):
            evaluate_listing([], self.business_date)


if __name__ == "__main__":
    unittest.main()
