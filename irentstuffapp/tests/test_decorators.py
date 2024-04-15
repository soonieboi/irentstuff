from django.test import TestCase
from unittest.mock import Mock
from django.http import HttpRequest, HttpResponse
from irentstuffapp.decorators import apply_standard_discount, apply_loyalty_discount

class MockResponse(HttpResponse):
    def __init__(self, context_data=None):
        super().__init__()
        self.context_data = context_data or {}

def mock_view(request, *args, **kwargs):
    return MockResponse(context_data={'item': kwargs.get('item')})

class MockItem:
    def __init__(self, price_per_day, discount_percentage=0, discounted_price=None):
        self.price_per_day = price_per_day
        self.discount_percentage = discount_percentage
        self.discounted_price = discounted_price

class ApplyStandardDiscountTestCase(TestCase):
    def test_apply_standard_discount(self):
        item = MockItem(price_per_day=100, discount_percentage=10)
        decorated_view = apply_standard_discount(mock_view)
        request = HttpRequest()

        response = decorated_view(request, item=item)
        
        self.assertIsNotNone(getattr(response.context_data.get('item', {}), 'discounted_price', None))
        self.assertEqual(response.context_data['item'].discounted_price, 90)

    
    def test_standard_discount_not_applied_when_zero_percentage(self):
        item = MockItem(price_per_day=100, discount_percentage=0)
        decorated_view = apply_standard_discount(mock_view)
        request = HttpRequest()

        response = decorated_view(request, item=item)

        self.assertIsNone(getattr(response.context_data.get('item', {}), 'discounted_price', None))

    
class ApplyLoyaltyDiscountTestCase(TestCase):
    def test_apply_loyalty_discount(self):
        item = MockItem(price_per_day=100, discount_percentage=0,discounted_price=90)
        request = HttpRequest()
        request.POST['apply_loyalty_discount'] = True
        request.user = Mock()

        decorated_view = apply_loyalty_discount(mock_view)
        response = decorated_view(request, item=item)
        
        self.assertIsNotNone(getattr(response.context_data.get('item', {}), 'discounted_price', None))
        self.assertEqual(response.context_data['item'].discounted_price, 90 * 0.95)

    def test_missing_loyalty_discount_flag(self):
        item = MockItem(price_per_day=100, discount_percentage=0, discounted_price=90)
        request = HttpRequest()
        request.user = Mock()
        
        decorated_view = apply_loyalty_discount(mock_view)
        response = decorated_view(request, item=item)
        
        self.assertEqual(response.context_data['item'].discounted_price, 90)

    def test_loyalty_discount_not_applied_without_initial_discounted_price(self):
        item = MockItem(price_per_day=100, discount_percentage=0)  
        request = HttpRequest()
        request.POST['apply_loyalty_discount'] = True
        request.user = Mock()

        decorated_view = apply_loyalty_discount(mock_view)
        response = decorated_view(request, item=item)

        self.assertIsNone(getattr(response.context_data.get('item', {}), 'discounted_price', None))

    def test_loyalty_discount_applied_directly(self):
        item = MockItem(price_per_day=100, discount_percentage=0, discounted_price=100)  
        request = HttpRequest()
        request.POST['apply_loyalty_discount'] = True
        request.user = Mock()

        decorated_view = apply_loyalty_discount(mock_view)
        response = decorated_view(request, item=item)

        self.assertEqual(response.context_data['item'].discounted_price, 100 * 0.95)
