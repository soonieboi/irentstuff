from django.utils import timezone

from .models import Item, Rental, Purchase, Message, Review


class ItemState:
    def __init__(self, context):
        self.context = context

    def view_active_rental_details(self, context):
        return context['user_state'].view_active_rental_details(context)

    def view_pending_purchase_details(self, context):
        return context['user_state'].view_pending_purchase_details(context)

    def view_item_messages(self, context):
        if isinstance(context['user_state'], ConcreteUserIsItemOwner):
            return Message.objects.filter(item=context['item'])

    def show_item_messages(self, context):
        if isinstance(context['user_state'], ConcreteUserIsItemOwner) and not Message.objects.filter(item=context['item']):
            return False
        else:
            return True

    def view_item_reviews(self, context):
        return Review.objects.filter(rental__item=context['item'])

    def view_item_reviews_by_user(self, context):
        if isinstance(context['user_state'], ConcreteUserIsNotItemOwner):
            return Rental.objects.filter(renter=context['user'], item=context['item'], status='completed')

    def can_cancel_rental(self, context):
        return False

    def can_accept_rental(self, context):
        return False

    def can_complete_rental(self, context):
        return False

    def can_add_rental(self, context):
        if isinstance(context['user_state'], ConcreteUserIsItemOwner) and not context['active_rental'] and not context['pending_purchase']:
            return True

    def can_cancel_purchase(self, context):
        return False

    def can_accept_purchase(self, context):
        return False

    def can_complete_purchase(self, context):
        return False

    def is_sold(self, context):
        if context['item'].availability == 'sold':
            return True
        else:
            return False

    def can_add_purchase(self, context):
        if isinstance(context['user_state'], ConcreteUserIsItemOwner) and not context['pending_purchase'] and not context['active_rental']:
            return True

    def can_edit_item(self, context):
        if isinstance(context['user_state'], ConcreteUserIsItemOwner) and not context['active_rental'] and not context['pending_purchase']:
            return True


class ConcreteRentalCompleted(ItemState):
    def can_accept_rental(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)


class ConcreteRentalPending(ItemState):
    def can_cancel_rental(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)

    def can_accept_rental(self, context):
        if isinstance(context['user_state'], ConcreteUserIsNotItemOwner):
            if context['active_rental'].start_date > timezone.now().date():
                return True


class ConcretePurchaseReserved(ItemState):
    def can_cancel_purchase(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)

    def can_accept_purchase(self, context):
        if isinstance(context['user_state'], ConcreteUserIsNotItemOwner):
            try:
                if context['pending_purchase'].deal_date > timezone.now().date():
                    return True
            except Exception:
                return False


class ConcreteRentalOrPurchaseOngoing(ItemState):
    def can_complete_rental(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)

    def can_complete_purchase(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)


class ConcretePurchaseCompleted(ItemState):
    def can_accept_purchase(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)


class UserState:
    def __init__(self, context):
        self.context = context


class ConcreteUserIsItemOwner(UserState):
    def is_sold(self, context):
        return Item.objects.filter(item=context['item'])

    def view_active_rental_details(self, context):
        return Rental.objects.filter(item=context['item']).exclude(status="completed").exclude(status="cancelled").first()

    def view_pending_purchase_details(self, context):
        return Purchase.objects.filter(item=context['item']).exclude(status="completed").exclude(status="cancelled").first()


class ConcreteUserIsNotItemOwner(UserState):
    def view_active_rental_details(self, context):
        try:
            rental_object = Rental.objects.filter(
                item=context['item'], renter=context['user']
                ).exclude(status="completed").exclude(status="cancelled").first()
        except Exception:
            rental_object = None
        return rental_object

    def view_pending_purchase_details(self, context):
        try:
            purchase_object = Purchase.objects.filter(
                item=context['item'], buyer=context['user']
                ).exclude(status="completed").exclude(status="cancelled").first()
        except Exception:
            purchase_object = None
        return purchase_object
