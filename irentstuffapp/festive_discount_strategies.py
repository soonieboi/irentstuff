import datetime


class DiscountStrategy:
    activation_date = None

    def calculate_discounted_deposit(self, deposit):
        raise NotImplementedError("Subclasses must implement calculate_discounted_deposit method")


class LabourDayDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 5, 1)

    def calculate_discounted_deposit(self, deposit):
        discount_description = 'Labour Day'
        discount_percentage = 0.05
        discount_price = float(deposit) * (1-discount_percentage)
        return discount_description, discount_percentage*100, discount_price


class VesakDayDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 5, 22)

    def calculate_discounted_deposit(self, deposit):
        discount_description = 'Vesak Day'
        discount_percentage = 0.07
        discount_price = float(deposit) * (1-discount_percentage)
        return discount_description, discount_percentage*100, discount_price


class HariRayaHajiDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 6, 17)

    def calculate_discounted_deposit(self, deposit):
        discount_description = 'Hari Raya Haji'
        discount_percentage = 0.1
        discount_price = float(deposit) * (1-discount_percentage)
        return discount_description, discount_percentage*100, discount_price


class TestDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 5, 4)

    def calculate_discounted_deposit(self, deposit):
        discount_description = 'Test'
        discount_percentage = 0.25
        discount_price = float(deposit) * (1-discount_percentage)
        return discount_description, discount_percentage*100, discount_price


class DefaultDiscountStrategy(DiscountStrategy):
    activation_date = None

    def calculate_discounted_deposit(self, deposit):
        discount_description = None
        discount_percentage = None
        discount_price = deposit
        return discount_description, discount_percentage, discount_price
