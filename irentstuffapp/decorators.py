from functools import wraps

def apply_standard_discount(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)

        if hasattr(response, 'context_data'):
            item = response.context_data.get('item')
            if item and item.discount_percentage > 0:
                discounted_price = item.price_per_day * (100 - item.discount_percentage) / 100
                item.discounted_price = discounted_price
        return response
    return _wrapped_view

def apply_loyalty_discount(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)

        # Assuming there's a method to check loyalty discount eligibility
        if hasattr(response, 'context_data'):
            item = response.context_data.get('item')
            user = request.user
            if 'apply_loyalty_discount' in request.POST and item.discounted_price:
                loyalty_discount_rate = 0.95  # Example 5% additional discount
                item.discounted_price *= loyalty_discount_rate

        return response
    return _wrapped_view
