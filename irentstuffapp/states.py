from .views import add_rental, edit_item, delete_item, item_messages, add_review, cancel_rental, item_messages
from .models import Rental, Message


class ItemState:
    def view_rental_details(self, context):
        return Rental.objects.filter(item=context.item)

    def view_item_messages(self, context):
        return Message.objects.filter(item=context.item)
    
    def add_rental_details(self, context):
        raise NotImplementedError()

    def edit_item(self, context):
        raise NotImplementedError()

    def delete_item(self, context):
        raise NotImplementedError()

    def add_review(self, context):
        raise NotImplementedError()

    def edit_rental_state(self, context):
        raise NotImplementedError()

    def add_item_message(self, context):
        raise NotImplementedError()    


class ConcreteItemAvailable(ItemState):
    def add_rental_details(self, context):
        if isinstance(context.user.state, ConcreteUserIsItemOwner):
            context.user.state.add_rental_details()
        else:
            raise ValueError("Cannot add rental details when user is not item owner")
    
    def edit_item(self, context):
        if isinstance(context.user.state, ConcreteUserIsItemOwner):
            context.user.state.edit_item()
        else:
            raise ValueError("Cannot edit item when user is not item owner")

    def delete_item(self, context):
        if isinstance(context.user.state, ConcreteUserIsItemOwner):
            context.user.state.delete_item()
        else:
            raise ValueError("Cannot delete item when user is not item owner")

    def add_item_message(self, context):
        if isinstance(context.user.state, ConcreteUserIsNotItemOwner):
            context.user.state.add_item_message()
        else:
            raise ValueError("Cannot delete item when user is not item owner")


class ConcreteItemCompleted(ItemState):
    def add_item_message(self, context):
        if isinstance(context.user.state, ConcreteUserIsNotItemOwner):
            context.user.state.add_review()
        else:
            raise ValueError("Cannot add message when user is item owner")


class ConcreteItemPending(ItemState):
    def edit_rental_state(self, context):
        if isinstance(context.user.state, ConcreteUserIsItemOwner):
            cancel_rental(context.request, context.item_id)
        else:
            raise ValueError("Cannot cancel rental when user is not item owner")


class ConcreteItemOngoing(ItemState):
    def edit_rental_state(self, context):
        if isinstance(context.user.state, ConcreteUserIsItemOwner):
            cancel_rental(context.request, context.item_id)
        else:
            raise ValueError("Cannot cancel rental when user is not item owner")


class UserState:
    def add_rental_details(self, context):
        pass

    def edit_item(self, context):
        pass

    def delete_item(self, context):
        pass

    def add_review(self, context):
        pass

    def add_item_message(self, context):
        pass


class ConcreteUserIsItemOwner(UserState):
    def add_rental_details(self, context):
        add_rental(context.request, context.item_id, username="")

    def edit_item(self, context):
        edit_item(context.request, context.item_id)

    def delete_item(self, context):
        delete_item(context.request, context.item_id)


class ConcreteUserIsNotItemOwner(UserState):
    def add_review(self, context):
        add_review(context.request, context.item_id)

    def add_item_message(self, context):
        item_messages(context.request, context.item_id, userid=0)
