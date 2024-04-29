from django.test import TestCase
from irentstuffapp.festive_discount_strategies import (
    DiscountStrategy, LabourDayDiscountStrategy, VesakDayDiscountStrategy,
    HariRayaHajiDiscountStrategy, TestDiscountStrategy, DefaultDiscountStrategy
    )


class DiscountStrategyTestCase(TestCase):
    def test_calculate_discounted_deposit_raises_not_implemented_error(self):
        strategy = DiscountStrategy()
        deposit = 100
        with self.assertRaises(NotImplementedError):
            strategy.calculate_discounted_deposit(deposit)

    def test_labour_day_discount(self):
        strategy = LabourDayDiscountStrategy()
        deposit = 100
        description, percentage, price = strategy.calculate_discounted_deposit(deposit)
        self.assertEqual(description, 'Labour Day')
        self.assertAlmostEqual(percentage, 5.0)
        self.assertAlmostEqual(price, 95.0)

    def test_vesak_day_discount(self):
        strategy = VesakDayDiscountStrategy()
        deposit = 100
        description, percentage, price = strategy.calculate_discounted_deposit(deposit)
        self.assertEqual(description, 'Vesak Day')
        self.assertAlmostEqual(percentage, 7.0)
        self.assertAlmostEqual(price, 93.0)

    def test_hari_raya_haji_discount(self):
        strategy = HariRayaHajiDiscountStrategy()
        deposit = 100
        description, percentage, price = strategy.calculate_discounted_deposit(deposit)
        self.assertEqual(description, 'Hari Raya Haji')
        self.assertAlmostEqual(percentage, 10.0)
        self.assertAlmostEqual(price, 90.0)

    def test_test_discount(self):
        strategy = TestDiscountStrategy()
        deposit = 100
        description, percentage, price = strategy.calculate_discounted_deposit(deposit)
        self.assertEqual(description, 'Test')
        self.assertAlmostEqual(percentage, 25.0)
        self.assertAlmostEqual(price, 75.0)

    def test_default_discount(self):
        strategy = DefaultDiscountStrategy()
        deposit = 100
        description, percentage, price = strategy.calculate_discounted_deposit(deposit)
        self.assertIsNone(description)
        self.assertIsNone(percentage)
        self.assertIsNone(price)
