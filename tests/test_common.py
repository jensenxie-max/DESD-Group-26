"""Boundary checks for the proposed shared availability calculation."""

from datetime import date
import unittest

from sprint2_demo.common import is_nonnegative_int, parse_date, sale_available


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.product = {"published": True, "quantity": 5, "startDate": "2026-11-12", "endDate": "2026-11-19"}

    def test_inclusive_boundaries_and_dates_outside_period(self):
        for day, expected in [(11, False), (12, True), (15, True), (19, True), (20, False)]:
            with self.subTest(day=day):
                self.assertEqual(sale_available(self.product, date(2026, 11, day)), expected)

    def test_zero_stock_and_unpublished_listing_are_unavailable(self):
        for patch in [{"quantity": 0}, {"published": False}]:
            with self.subTest(patch=patch):
                self.assertFalse(sale_available(self.product | patch, date(2026, 11, 15)))

    def test_invalid_dates_do_not_silently_become_available(self):
        for value in ["2026-02-30", "20261112", "2026-1-12", " 2026-11-12", None, 20261112]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_date(value)

    def test_boolean_is_not_a_stock_count(self):
        self.assertFalse(is_nonnegative_int(True))
        self.assertFalse(is_nonnegative_int(False))
        self.assertTrue(is_nonnegative_int(0))
        self.assertFalse(is_nonnegative_int(1.5))
        self.assertFalse(is_nonnegative_int(-1))

    def test_reversed_period_is_rejected(self):
        with self.assertRaises(ValueError):
            sale_available(self.product | {"endDate": "2026-11-01"}, date(2026, 11, 15))


if __name__ == "__main__":
    unittest.main()
