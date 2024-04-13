from .models import Rental, Message, Review
from django.utils import timezone


class ItemState:
    def __init__(self, context):
        self.context = context

    def view_active_rental_details(self, context):
        return context['user_state'].view_active_rental_details(context)

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
        if isinstance(context['user_state'], ConcreteUserIsItemOwner) and not context['active_rental']:
            return True
        
    def can_edit_item(self, context):
        if isinstance(context['user_state'], ConcreteUserIsItemOwner) and not context['active_rental']:
            return True


class ConcreteRentalCompleted(ItemState):
    def can_accept_rental(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)


class ConcreteRentalPending(ItemState):
    def can_cancel_rental(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)
    
    def can_accept_rental(self, context):
        if isinstance(context['user_state'], ConcreteUserIsNotItemOwner):
            if context['active_rental'].start_date>timezone.now().date():
                return True


class ConcreteRentalOngoing(ItemState):
    def can_complete_rental(self, context):
        return isinstance(context['user_state'], ConcreteUserIsItemOwner)


class UserState:
    def __init__(self, context):
        self.context = context

class ConcreteUserIsItemOwner(UserState):
    def view_active_rental_details(self, context):
        return Rental.objects.filter(item=context['item']).exclude(status="completed").exclude(status="cancelled").first()


class ConcreteUserIsNotItemOwner(UserState):
    def view_active_rental_details(self, context):
        return Rental.objects.filter(item=context['item'], renter = context['user']).exclude(status="completed").exclude(status="cancelled").first()
