from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from .decorators import apply_standard_discount, apply_loyalty_discount
from .forms import ItemForm, ItemEditForm, RentalForm, MessageForm, ItemReviewForm, PurchaseForm
from .models import (Item, Rental, Message, Category, Purchase,
                     ItemStatesCaretaker, RentalEmailSender, RentalMessageSender, PurchaseEmailSender, PurchaseMessageSender,
                     Interest, UserInterests, Top3CategoryDisplay, ItemsDiscountDisplay, NewlyListedItemsDisplay
                     )
from .states import (
    ItemState, ConcreteRentalPending, ConcretePurchaseReserved, ConcreteRentalOrPurchaseOngoing,
    ConcreteUserIsItemOwner, ConcreteUserIsNotItemOwner
)

import logging

logging.basicConfig(level=logging.DEBUG)


def index(request):
    return HttpResponse("Index")


# common function to manage the discount price displayed on the items list
def items_discount_price(items):
    for item in items:
        if item.discount_percentage > 0:
            discounted_price = item.price_per_day * (100 - item.discount_percentage) / 100
            item.discounted_price = discounted_price
        else:
            item.discounted_price = item.price_per_day
    return items


@apply_standard_discount
def items_list(request):

    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    # Check for any festive discounts on purchase price
    for item in Item.objects.all():
        if item.festive_discounts and item.availability == 'available':
            try:
                item.calculate_festive_discount_price()
            except Exception:
                # This exception ensures that in the edge case where the day changes (e.g. past 12mn) the festive discount details are reset
                item.festive_discount_description = item.festive_discount_percentage = item.festive_discount_price = None
                item.save()
        if item.festive_discounts is False:
            item.festive_discount_description = item.festive_discount_percentage = item.festive_discount_price = None
            item.save()

    if request.user.is_authenticated and request.resolver_match.url_name == 'items_list_my':
        items = Item.objects.filter(owner=request.user)
    else:
        items = Item.objects.all()

    if search_query:
        items = items.filter(title__icontains=search_query)

    if category_filter:
        items = items.filter(category__name__iexact=category_filter)

    categories = Category.objects.all()
    items = items_discount_price(items)

    context = {
        'items': items,
        'categories': categories,
        'searchstr': search_query,
        'selected_category': category_filter,
        'no_items_message': not items.exists(),
        'mystuff': request.resolver_match.url_name == 'items_list_my'
    }

    return render(request, 'irentstuffapp/items.html', context)


@login_required
def deals_view(request):
    try:
        user_interests = UserInterests.objects.get(user=request.user)
        template = ItemsDiscountDisplay()
        items = template.get_items(user_interests.interest)
        items = items_discount_price(items)

        return render(request, 'irentstuffapp/items.html', {'items': items, 'no_items_message': not items.exists()})
    except UserInterests.DoesNotExist:
        return redirect('interest')


@login_required
def new_items_view(request):
    try:
        user_interests = UserInterests.objects.get(user=request.user)
        template = NewlyListedItemsDisplay()
        items = template.get_items(user_interests.interest)
        items = items_discount_price(items)

        return render(request, 'irentstuffapp/items.html', {'items': items, 'no_items_message': not items.exists()})
    except UserInterests.DoesNotExist:
        return redirect('interest')


@login_required
def fav_categories_view(request):
    try:
        user_interests = UserInterests.objects.get(user=request.user)
        template = Top3CategoryDisplay()
        items = template.get_items(user_interests.interest)
        items = items_discount_price(items)

        return render(request, 'irentstuffapp/items.html', {'items': items, 'no_items_message': not items.exists()})
    except UserInterests.DoesNotExist:
        return redirect('interest')


@login_required
@apply_loyalty_discount
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user  # Set the item's creator to the logged-in user
            item.created_date = timezone.now()
            item.availability = 'available'
            item.save()
            save_state(request, item.id)
            return redirect('item_detail', item_id=item.id)  # Redirect to item detail page
    else:
        form = ItemForm()

    return render(request, 'irentstuffapp/item_add.html', {'form': form})


@login_required
def add_review(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    user = request.user
    form = ItemReviewForm(user, item, request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            review = form.save(commit=False)
            review.author = user
            review.created_date = timezone.now()
            review.save()

            return redirect('item_detail', item_id=item_id)  # Redirect to item detail page

    return render(request, 'irentstuffapp/review_add.html', {'form': form, 'item': item})


@apply_loyalty_discount
def item_detail_with_state_pattern(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    is_owner = request.user == item.owner
    # msgshow = True
    undos = False
    
    # Check for any festive discounts on purchase price
    if item.festive_discounts and item.availability == 'available':
        try:
            item.calculate_festive_discount_price()
        except Exception:
            # This exception ensures that in the edge case where the day changes (e.g. past 12mn) the festive discount details are reset
            item.festive_discount_description = item.festive_discount_percentage = item.festive_discount_price = None
            item.save()
    if item.festive_discounts is False:
        item.festive_discount_description = item.festive_discount_percentage = item.festive_discount_price = None
        item.save()

    context = {'item': item, 'user': request.user}

    if is_owner:
        user_state = ConcreteUserIsItemOwner(context)
    else:
        user_state = ConcreteUserIsNotItemOwner(context)

    context.update({'user_state': user_state})

    concrete_item_state = ItemState(context)
    reviews = concrete_item_state.view_item_reviews(context)
    # check if there are any messages related to this item
    # item_messages = concrete_item_state.view_item_messages(context)

    msgshow = concrete_item_state.show_item_messages(context)

    renter = None
    make_review = False

    if request.user.is_authenticated:
        active_rentals_obj = concrete_item_state.view_active_rental_details(context)
        pending_purchase_obj = concrete_item_state.view_pending_purchase_details(context)

        context['active_rental'] = active_rentals_obj
        context['pending_purchase'] = pending_purchase_obj

        if active_rentals_obj:

            renter = active_rentals_obj.renter
            context.update({'renter': renter})

            # can cancel?
            # can accept?
            # Check if there is a rental offer for this item - pending - before start_date
            # accept_rental_obj = active_rentals_obj.filter(status='pending', start_date__gt=timezone.now()).first()
            # if accept_rental_obj:
            if active_rentals_obj.status == 'pending':
                concrete_item_state = ConcreteRentalPending(context)

            # can complete?
            elif active_rentals_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context)

        if pending_purchase_obj:

            buyer = pending_purchase_obj.buyer
            context.update({'buyer': buyer})

            if pending_purchase_obj.status == 'reserved':
                concrete_item_state = ConcretePurchaseReserved(context)

            # can complete?
            elif pending_purchase_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context)

        else:
            # check if user has undos for this item
            caretakercount = ItemStatesCaretaker.objects.filter(item=item).count()
            if caretakercount > 1:
                undos = True

            # check if there are any completed rentals that user may want to review
            review_obj = concrete_item_state.view_item_reviews_by_user(context)
            if review_obj:
                make_review = True

    cancel_rental = concrete_item_state.can_cancel_rental(context)
    accept_rental = concrete_item_state.can_accept_rental(context)
    complete_rental = concrete_item_state.can_complete_rental(context)
    add_rental = concrete_item_state.can_add_rental(context)
    cancel_purchase = concrete_item_state.can_cancel_purchase(context)
    accept_purchase = concrete_item_state.can_accept_purchase(context)
    complete_purchase = concrete_item_state.can_complete_purchase(context)
    add_purchase = concrete_item_state.can_add_purchase(context)
    edit_item = concrete_item_state.can_edit_item(context)
    is_sold = concrete_item_state.is_sold(context)

    if item.discount_percentage > 0:
        discounted_price = item.price_per_day * (100 - item.discount_percentage) / 100
        item.discounted_price = discounted_price

    context.update({'is_owner': is_owner,
                    'is_sold': is_sold,
                    'make_review': make_review,
                    'add_rental': add_rental,
                    'accept_rental': accept_rental,
                    'complete_rental': complete_rental,
                    'cancel_rental': cancel_rental,
                    'add_purchase': add_purchase,
                    'accept_purchase': accept_purchase,
                    'complete_purchase': complete_purchase,
                    'cancel_purchase': cancel_purchase,
                    'edit_item': edit_item,
                    'mystuff': request.resolver_match.url_name == 'items_list_my',
                    'msgshow': msgshow,
                    'reviews': reviews,
                    'undos': undos})
    return render(request, 'irentstuffapp/item_detail.html', context)


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the user is the owner of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)
    
    # add logic to find if there is an associated existing rental
    pending_rental = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if pending_rental.exists():
        messages.error(request, 'You cannot edit an item when rental status is Pending or Confirmed!')
        return redirect('item_detail', item_id=item.id)

    # add logic to find if there is an associated existing purchase
    pending_purchases = Purchase.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if pending_purchases.exists():
        messages.error(request, 'You cannot edit an item when purchase status is Reserved or Confirmed!')
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        form = ItemEditForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()

            # Call save_state to save the current state of the item
            save_state(request, item_id)

            return redirect('item_detail', item_id=item.id)
    else:
        form = ItemEditForm(instance=item)

    return render(request, 'irentstuffapp/item_edit.html', {'item': item, 'form': form})


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the creator of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)

    # add logic to find if associated rental confirmed/pending
    pending_rental = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if pending_rental.exists():
        messages.error(request, 'You cannot delete an item when rental status is Pending or Confirmed!')
        return redirect('item_detail', item_id=item.id)

    pending_purchases = Purchase.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if pending_purchases.exists():
        messages.error(request, 'You cannot delete an item when purchase status is Reserved or Confirmed!')
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        delete_confirm = request.POST.get('delete_confirm', '')
        if delete_confirm == 'confirmed':
            item.delete()
            return redirect('items_list')  # Redirect to items list after deletion
        else:
            # User cancelled deletion, redirect back to item detail page
            return redirect('item_detail', item_id=item.id)
    return redirect('items_list')  # Redirect to the items list page or another appropriate page


@login_required
def save_state(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the owner of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return HttpResponseForbidden()

    caretaker = ItemStatesCaretaker.objects.filter(item=item).first()
    if not caretaker:
        caretaker = ItemStatesCaretaker(item=item)

    caretaker.save_state()  # Save the current state of the item

    # messages.success(request, 'State saved successfully!')
    return redirect('item_detail', item_id=item_id)


@login_required
def restore_state(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the owner of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return HttpResponseForbidden()

    # don't delete if only 1 state, that is the original state
    caretakercount = ItemStatesCaretaker.objects.filter(item=item).count()

    if caretakercount < 2:
        messages.error(request, 'No previous changes found for this item.')
        return redirect('item_detail', item_id=item_id)

    caretakerdel = ItemStatesCaretaker.objects.filter(item=item).order_by('-datetime_saved').first()

    if caretakerdel:
        caretakerdel.delete()

    caretaker = ItemStatesCaretaker.objects.filter(item=item).order_by('-datetime_saved').first()
    if not caretaker or not caretaker.memento:
        messages.error(request, 'No changes found for this item.')
        return redirect('item_detail', item_id=item_id)

    caretaker.restore_state()  # Restore the item to the previous state

    messages.success(request, 'Undo was successful!')
    return redirect('item_detail', item_id=item_id)


@login_required
def item_messages(request, item_id, userid=0):

    item = get_object_or_404(Item, pk=item_id)

    # owner view of messages from every user who enquired
    if userid == 0 and item.owner == request.user:

        # Group messages by enquiring_user_id and count the number of messages for each user
        grouped_messages = Message.objects.filter(item=item).values('enquiring_user', 'enquiring_user__username').annotate(message_count=Count('id'))

        return render(request, 'irentstuffapp/item_messages_list.html', {'item': item, 'grouped_messages': grouped_messages})

    else:

        # enquiring_user = User.objects.filter(id=userid).first()

        if item.owner == request.user:
            enquiring_user = User.objects.filter(id=userid).first()
        else:
            enquiring_user = request.user

        if request.method == 'POST':
            message_form = MessageForm(request.POST)
            if message_form.is_valid():
                message = message_form.save(commit=False)
                message.sender = request.user
                if request.user == item.owner:
                    message.recipient = enquiring_user
                else:
                    message.recipient = item.owner

                message.item = item
                message.enquiring_user = enquiring_user
                message.subject = 'message'
                message.timestamp = timezone.now()
                message.save()

                subject = 'iRentStuff.app - You have a message'
                html_message = render_to_string('emails/enquiry_received_email.html', {'message': message})
                plain_message = strip_tags(html_message)
                email_from = settings.DEFAULT_FROM_EMAIL

                email = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    email_from,
                    [message.recipient.email],
                )
                email.attach_alternative(html_message, "text/html")
                email.send()

                if request.user == item.owner:
                    return redirect('item_messages', item_id=item.id, userid=enquiring_user.id)

                else:
                    return redirect('item_messages_list', item_id=item.id)

                # messages.success(request, 'Rental added successfully!')
                # return redirect('item_detail', item_id=item.id)
                # return redirect(reverse('current_url_name'))
                # return render(request, 'irentstuffapp/item_messages.html', {'item': item, 'enquiring_user':enquiring_user.username,
                #                                                             'item_messages': item_messages, 'message_form': message_form})

                # item_messages = Message.objects.filter(item=item, enquiring_user = userid).order_by('timestamp')

                # return render(request, 'irentstuffapp/item_messages.html', {'item': item, 'enquiring_user':enquiring_user.username,
                #                                                             'item_messages': item_messages, 'message_form': message_form})
        else:
            message_form = MessageForm(initial={'item': item, 'recipient': item.owner})

        # set messages to is_read
        item_incoming_msgs = Message.objects.filter(item=item, enquiring_user=enquiring_user, is_read=False).exclude(sender=request.user.id)
        for itmmsg in item_incoming_msgs:
            itmmsg.is_read = True
            itmmsg.save()

        active_rentals = False
        accept_rental = False
        pending_purchase = False
        accept_purchase = False
        if item.owner == request.user:
            # Check if there are active rentals for this item
            active_rentals_obj = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled").first()
            pending_purchase_obj = Purchase.objects.filter(item=item).exclude(status="complete").exclude(status="cancelled").first()

            if active_rentals_obj:
                active_rentals = True
            if pending_purchase_obj:
                pending_purchase = True
        else:
            # Check if there is a rental offer for this item - pending - before start_date
            accept_rental_obj = Rental.objects.filter(item=item, renter=request.user, status='pending', start_date__gt=timezone.now()).first()
            accept_purchase_obj = Purchase.objects.filter(item=item, buyer=request.user, status='reserved', deal_date__gt=timezone.now()).first()

            if accept_rental_obj:
                accept_rental = True
            if accept_purchase_obj:
                accept_purchase = True

        item_messages = Message.objects.filter(item=item, enquiring_user=enquiring_user).order_by('timestamp')
        return render(request, 'irentstuffapp/item_messages.html',
                      {'item': item,
                       'enquiring_user': enquiring_user.username,
                       'item_messages': item_messages,
                       'message_form': message_form,
                       'active_rentals': active_rentals,
                       'accept_rental': accept_rental,
                       'pending_purchase': pending_purchase,
                       'accept_purchase': accept_purchase})


@login_required
def inbox(request):

    # Group messages by enquiring_user_id and count the number of messages for each user
    grouped_messages = Message.objects.filter(recipient=request.user.id).values(
        'enquiring_user', 'enquiring_user__username', 'item__id', 'item__title'
        ).annotate(message_count=Count('id'))

    return render(request, 'irentstuffapp/inbox.html', {'grouped_messages': grouped_messages})


@login_required
@apply_loyalty_discount
def add_rental(request, item_id, username=""):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the creator of the item
    if request.user != item.owner:
        # Optionally, you can handle unauthorized access here
        return redirect('item_detail', item_id=item.id)

    if item.availability == 'sold':
        messages.error(request, '''Item has been sold. You cannot rent it out. To rent out another copy of this item,
                       please create a new entry using the "Add Stuff" button.''')
        return redirect('item_detail', item_id=item.id)

    # Check if there are active rentals for the item
    active_rentals = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if active_rentals.exists():
        messages.error(request, 'There are active rentals for this item. You cannot add a new rental.')
        return redirect('item_detail', item_id=item.id)

    pending_purchases = Purchase.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if pending_purchases.exists():
        messages.error(request, 'There are pending purchases for this item. You cannot add a new rental.')
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        form = RentalForm(request.POST)

        # Check if the logged-in user is the creator, owner, or renter of the item
        if request.user.username == form['renterid'].value():
            messages.error(request, 'You cannot rent your own item.')
            return redirect('item_detail', item_id=item.id)
        
        if form.is_valid():

            renterid = form['renterid'].value()

            rental = form.save(commit=False)

            rentaluser = User.objects.filter(username=renterid).first()
            rental.renter = rentaluser

            rental.item = item  # Set the item for the rental
            rental.owner = request.user  # Set the owner to the logged-in user
            rental.pending_date = timezone.now()
            rental.status = 'pending'

            rental_email_sender = RentalEmailSender()
            rental_message_sender = RentalMessageSender()

            # Register observers with the rental object
            rental.add_observer(rental_email_sender)
            rental.add_observer(rental_message_sender)

            rental.save()
            rental.notify_observers()

            # Update the status of the item to indicate that there is an active rental
            item.availability = 'active_rental'
            item.save()

            return redirect('item_detail', item_id=item.id)

    else:
        form = RentalForm()
        if username:
            form['renterid'].initial = username

    return render(request, 'irentstuffapp/rental_add.html', {'form': form, 'item': item})


@login_required
def accept_rental(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is renter
    accept_rental_obj = Rental.objects.filter(item=item, renter=request.user, status='pending', start_date__gt=timezone.now()).first()
    if accept_rental_obj:
        rental_email_sender = RentalEmailSender()
        rental_message_sender = RentalMessageSender()

        # Register observers with the rental object
        accept_rental_obj.add_observer(rental_email_sender)
        accept_rental_obj.add_observer(rental_message_sender)

        accept_rental_obj.change_state('confirmed')

    return redirect('item_detail', item_id=item.id)


@login_required
def complete_rental(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is owner and status is confirmed
    complete_rental_obj = Rental.objects.filter(item=item, owner=request.user, status='confirmed').first()
    if complete_rental_obj:
        rental_email_sender = RentalEmailSender()
        rental_message_sender = RentalMessageSender()

        # Register observers with the rental object
        complete_rental_obj.add_observer(rental_email_sender)
        complete_rental_obj.add_observer(rental_message_sender)

        complete_rental_obj.change_state('completed')

        # Update the status of the item to indicate that it is now available again
        item.availability = 'available'
        item.save()

    return redirect('item_detail', item_id=item.id)


@login_required
def cancel_rental(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is owner and status is confirmed
    cancel_rental_obj = Rental.objects.filter(item=item, owner=request.user, status='pending').first()
    if cancel_rental_obj:
        rental_email_sender = RentalEmailSender()
        rental_message_sender = RentalMessageSender()

        # Register observers with the rental object
        cancel_rental_obj.add_observer(rental_email_sender)
        cancel_rental_obj.add_observer(rental_message_sender)

        cancel_rental_obj.change_state('cancelled')

        # Update the status of the item to indicate that it is now available again
        item.availability = 'available'
        item.save()

    return redirect('item_detail', item_id=item.id)


@login_required
def add_purchase(request, item_id, username=""):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is the creator of the item
    if request.user != item.owner:
        return redirect('item_detail', item_id=item.id)

    # Redirect if item is sold
    if item.availability == 'sold':
        messages.error(request, '''Item has been sold. You cannot sell it again. To rent out another copy of this item,
                please create a new entry using the "Add Stuff" button.''')
        return redirect('item_detail', item_id=item.id)

    # Redirect if item is rented out
    active_rentals = Rental.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if active_rentals.exists():
        messages.error(request, 'There are active rentals for this item. You cannot add a new purchase.')
        return redirect('item_detail', item_id=item.id)

    # Redirect if item is pending to be purchased
    pending_purchases = Purchase.objects.filter(item=item).exclude(status="completed").exclude(status="cancelled")
    if pending_purchases.exists():
        messages.error(request, 'There are pending purchases for this item. You cannot add a new purchase.')
        return redirect('item_detail', item_id=item.id)

    # Recalculate festive discount price so that it is accurate

    # Check for any festive discounts on purchase price
    if item.festive_discounts and item.availability == 'available':
        try:
            item.calculate_festive_discount_price()
        except Exception:
            # This exception ensures that in the edge case where the day changes (e.g. past 12mn) the festive discount details are reset
            item.festive_discount_description = item.festive_discount_percentage = item.festive_discount_price = None
            item.save()
    if item.festive_discounts is False:
        item.festive_discount_description = item.festive_discount_percentage = item.festive_discount_price = None
        item.save()

    festive_discount_description = item.festive_discount_description
    festive_discount_percentage = item.festive_discount_percentage
    festive_discount_price = item.festive_discount_price

    if request.method == 'POST':
        form = PurchaseForm(request.POST)

        # Check if the logged-in user is the creator, owner, or buyer of the item
        if request.user.username == form['buyerid'].value():
            messages.error(request, 'You cannot purchase your own item.')
            return redirect('item_detail', item_id=item.id)
        
        if form.is_valid():

            buyerid = form['buyerid'].value()

            purchase = form.save(commit=False)

            purchaseuser = User.objects.filter(username=buyerid).first()
            purchase.buyer = purchaseuser

            purchase.item = item  # Set the item for the purchase
            purchase.owner = request.user  # Set the owner to the logged-in user
            purchase.reserved_date = timezone.now()
            purchase.status = 'reserved'

            purchase_email_sender = PurchaseEmailSender()
            purchase_message_sender = PurchaseMessageSender()

            # Register observers with the purchase object
            purchase.add_observer(purchase_email_sender)
            purchase.add_observer(purchase_message_sender)

            purchase.save()
            purchase.notify_observers()

            # Update the status of the item to indicate that it is now available again
            item.availability = 'pending_purchase'
            item.save()

            return redirect('item_detail', item_id=item.id)

    else:
        form = PurchaseForm()
        if username:
            form['buyerid'].initial = username

    return render(request, 'irentstuffapp/purchase_add.html', {
        'form': form,
        'item': item,
        'festive_discount_description': festive_discount_description,
        'festive_discount_price': festive_discount_price,
        'festive_discount_percentage': festive_discount_percentage})


@login_required
def accept_purchase(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is buyer
    accept_purchase_obj = Purchase.objects.filter(item=item, buyer=request.user, status='reserved', deal_date__gt=timezone.now()).first()
    if accept_purchase_obj:
        purchase_email_sender = PurchaseEmailSender()
        purchase_message_sender = PurchaseMessageSender()

        # Register observers with the purchase object
        accept_purchase_obj.add_observer(purchase_email_sender)
        accept_purchase_obj.add_observer(purchase_message_sender)

        accept_purchase_obj.change_state('confirmed')

    return redirect('item_detail', item_id=item.id)


@login_required
def complete_purchase(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is owner and status is confirmed
    complete_purchase_obj = Purchase.objects.filter(item=item, owner=request.user, status='confirmed').first()
    if complete_purchase_obj:
        purchase_email_sender = PurchaseEmailSender()
        purchase_message_sender = PurchaseMessageSender()

        # Register observers with the purchase object
        complete_purchase_obj.add_observer(purchase_email_sender)
        complete_purchase_obj.add_observer(purchase_message_sender)

        complete_purchase_obj.change_state('completed')

        # Update the status of the item to indicate that it is now available again
        item.availability = 'sold'
        item.save()

    return redirect('item_detail', item_id=item.id)


@login_required
def cancel_purchase(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Check if the logged-in user is owner and status is confirmed
    cancel_purchase_obj = Purchase.objects.filter(item=item, owner=request.user, status='reserved').first()
    if cancel_purchase_obj:
        purchase_email_sender = PurchaseEmailSender()
        purchase_message_sender = PurchaseMessageSender()

        # Register observers with the purchase object
        cancel_purchase_obj.add_observer(purchase_email_sender)
        cancel_purchase_obj.add_observer(purchase_message_sender)

        cancel_purchase_obj.change_state('cancelled')

        # Update the status of the item to indicate that it is now available again
        item.availability = 'available'
        item.save()

    return redirect('item_detail', item_id=item.id)


def check_user_exists(request, username):
    user_exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': user_exists})


def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        firstname = request.POST.get('fname')
        lastname = request.POST.get('lname')
        username = request.POST.get('uname')
        if User.objects.filter(email=email).exists():
            messages.warning(request, 'User with this email already exists')
            return redirect('register')
        else:
            user = User(email=email, password=password, first_name=firstname,
                        last_name=lastname, username=username)
            user.set_password(password)
            user.save()

            subject = 'Welcome to iRentStuff.app - Your Account Registration is Successful!'
            html_message = render_to_string('emails/welcome_email.html', {'user_name': username})
            plain_message = strip_tags(html_message)
            email_from = settings.DEFAULT_FROM_EMAIL

            email = EmailMultiAlternatives(
                subject,
                plain_message,
                email_from,
                [email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            messages.success(request, 'Thank you for your registration! You may log in now')
            return redirect('/login')
    return render(request, 'irentstuffapp/register.html')


def login_user(request):
    if request.method == 'POST':
        username = request.POST['uname']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.warning(request, 'Invalid Credentials')
            return redirect('login')
    return render(request, 'irentstuffapp/login.html')


@login_required
def logout_user(request):
    logout(request)
    return redirect('/')


# interest form for user to indicate category they like, items created within past 3 days by default
@login_required
def category_interest(request):
    categories = Category.objects.all()
    existing_user_interests = UserInterests.objects.filter(user=request.user).first()

    context = {
        'categories': categories,
        'existing_user_interests': existing_user_interests,
    }

    if request.method == 'POST':
        selected_categories = request.POST.get('selected_categories')
        item_cd_crit = request.POST.get('item_cd_crit')
        # existing_user_interests = UserInterests.objects.filter(user=request.user).first()

        if selected_categories:
            selected_categories_list = selected_categories.split(',')

            old_interests = Interest.objects.filter(created_date__lte=timezone.now())
            if old_interests.exists():
                old_interests.delete()

            interest = Interest.objects.create(created_date=timezone.now(), discount=True, item_cd_crit=item_cd_crit)
            interest.categories.add(*selected_categories_list)
            interest.save()

        if existing_user_interests:
            existing_user_interests.interest = interest

            existing_user_interests.save()
            return redirect('items_list')
        else:
            user_interests = UserInterests.objects.create(user=request.user, interest=interest)
            user_interests.save()
            return redirect('items_list')

    return render(request, 'irentstuffapp/interest.html', context)
