from django.utils import timezone
import datetime


class Meta(type):
    registry = []

    def __new__(cls, name, bases, attrs):
        cls_obj = super().__new__(cls, name, bases, attrs)
        Meta.registry.append(cls_obj)
        return cls_obj

    @classmethod
    def get_subclasses(cls):
        return cls.registry


class DiscountStrategy(metaclass=Meta):
    activation_date = None

    def calculate_discounted_deposit(self, deposit):
        discount_description, discount_percentage = self.get_discount_details(deposit)
        if discount_percentage:
            discount_price = float(deposit) * (1-(discount_percentage*0.01))
        else:
            discount_price = None
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
    activation_date = datetime.date(2024, 5, 4)

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


def get_discount_strategy():
    strategies = DiscountStrategy.get_subclasses()

    # Use undiscounted strategy as default
    discount_strategy = DefaultDiscountStrategy()

    # Iterate through strategies to check if activation_date matches today
    for strategy_class in strategies:
        if timezone.now().date() == strategy_class.activation_date:
            discount_strategy = strategy_class()
            break

    return discount_strategy