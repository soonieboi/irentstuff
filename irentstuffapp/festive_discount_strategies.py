import datetime


class DiscountStrategy:
    activation_date = None

    def calculate_discounted_deposit(self, deposit):
        discount_description, discount_percentage = self.get_discount_details(deposit)
        discount_price = float(deposit) * (1-(discount_percentage*0.01))
        return discount_description, discount_percentage, discount_price

    def get_discount_details(self, deposit):
        raise NotImplementedError("Subclasses must implement calculate_discounted_deposit method")


class LabourDayDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 5, 1)

    def get_discount_details(self, deposit):
        discount_description = 'Labour Day'
        discount_percentage = 5
        return discount_description, discount_percentage


class VesakDayDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 5, 22)

    def get_discount_details(self, deposit):
        discount_description = 'Vesak Day'
        discount_percentage = 7
        return discount_description, discount_percentage


class HariRayaHajiDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 6, 17)

    def get_discount_details(self, deposit):
        discount_description = 'Hari Raya Haji'
        discount_percentage = 10
        return discount_description, discount_percentage


class TestDiscountStrategy(DiscountStrategy):
    activation_date = datetime.date(2024, 4, 29)

    def get_discount_details(self, deposit):
        discount_description = 'Test'
        discount_percentage = 25
        return discount_description, discount_percentage


class DefaultDiscountStrategy(DiscountStrategy):
    activation_date = None

    def get_discount_details(self, deposit):
        discount_description = None
        discount_percentage = None
        return discount_description, discount_percentage
