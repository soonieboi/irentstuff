from abc import ABC, abstractmethod
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .festive_discount_strategies import (
    DefaultDiscountStrategy,
    LabourDayDiscountStrategy,
    HariRayaHajiDiscountStrategy,
    VesakDayDiscountStrategy,
    TestDiscountStrategy
    )


def send_email(subject, message, email_to):
    email_from = settings.DEFAULT_FROM_EMAIL
    plain_message = strip_tags(message)
    email = EmailMultiAlternatives(
        subject,
        plain_message,
        email_from,
        [email_to],
    )
    email.attach_alternative(message, "text/html")
    email.send()


# Define the Observer interface
class RentalObserver(ABC):
    @abstractmethod
    def update(self, rental):
        pass


# Implement concrete Observers (classes responsible for sending emails and messages)
class RentalEmailSender(RentalObserver):
    def update(self, rental):
        # Logic to send email to the renter or owner based on rental state change
        rental_message = "email sender received update from rental "
        print(rental_message + rental.item.title + " " + rental.status + " " + rental.renter.username + " " + rental.owner.username)

        if rental.status == 'pending':
            subject = 'iRentStuff.app - You added a Rental'
            html_message = render_to_string('emails/rental_added_email.html', {'rental': rental})
            send_email(subject, html_message, rental.owner.email)

            subject2 = 'iRentStuff.app - You have a Rental Offer'
            html_message2 = render_to_string('emails/rental_added_email2.html', {'rental': rental})
            send_email(subject2, html_message2, rental.renter.email)

        elif rental.status == 'confirmed':
            subject = 'iRentStuff.app - you have a Rental Acceptance'
            html_message = render_to_string('emails/rental_confirmed_email.html', {'rental': rental})
            send_email(subject, html_message, rental.owner.email)

            subject2 = 'iRentStuff.app - You accepted a Rental Offer'
            html_message2 = render_to_string('emails/rental_confirmed_email2.html', {'rental': rental})
            send_email(subject2, html_message2, rental.renter.email)

        elif rental.status == 'completed':
            subject = 'iRentStuff.app - you have set a rental to Complete'
            html_message = render_to_string('emails/rental_completed_email.html', {'rental': rental})
            send_email(subject, html_message, rental.owner.email)

        elif rental.status == 'cancelled':
            subject = 'iRentStuff.app - you have cancelled a rental'
            html_message = render_to_string('emails/rental_cancelled_email.html', {'rental': rental})
            send_email(subject, html_message, rental.owner.email)


class RentalMessageSender(RentalObserver):
    def update(self, rental):
        # Logic to send message to the renter or owner based on rental state change

        if rental.status == 'pending':
            message = Message()
            message.item = rental.item
            message.enquiring_user = rental.renter
            message.sender = User.objects.get(id=1)
            message.recipient = rental.renter
            message.subject = 'Admin'
            message.content = 'Rental has been offered. Period of rental is from ' + str(rental.start_date) + ' to ' + str(rental.end_date)
            message.timestamp = timezone.now()
            message.save()
        elif rental.status == 'confirmed':
            message = Message()
            message.item = rental.item
            message.enquiring_user = rental.renter
            message.sender = User.objects.get(id=1)
            message.recipient = rental.owner
            message.subject = 'Admin'
            message.content = 'Rental has been accepted. Period of rental is from ' + str(rental.start_date) + ' to ' + str(rental.end_date)
            message.timestamp = timezone.now()
            message.save()
        elif rental.status == 'completed':
            message = Message()
            message.item = rental.item
            message.enquiring_user = rental.renter
            message.sender = User.objects.get(id=1)
            message.recipient = rental.renter
            message.subject = 'Admin'
            message.content = 'Rental has been completed. Period of rental is from ' + str(rental.start_date) + ' to ' + str(rental.end_date)
            message.timestamp = timezone.now()
            message.save()
        elif rental.status == 'cancelled':
            message = Message()
            message.item = rental.item
            message.enquiring_user = rental.renter
            message.sender = User.objects.get(id=1)
            message.recipient = rental.renter
            message.subject = 'Admin'
            message.content = 'Rental has been cancelled.'
            message.timestamp = timezone.now()
            message.save()


# Extend Decimal to prevent negative values
class PositiveDecimalField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(MinValueValidator(0.01, message='Value should be at least 0.01.'))


class Item(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    condition = models.CharField(max_length=255, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')])
    availability = models.CharField(max_length=255, choices=[
        ('available', 'Available'), ('active_rental', 'Active Rental'), ('pending_purchase', 'Pending Purchase'), ('sold', 'Sold')
        ], default='available')
    price_per_day = PositiveDecimalField(max_digits=10, decimal_places=2)
    deposit = PositiveDecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='item_images/')
    created_date = models.DateTimeField(blank=True)
    deleted_date = models.DateTimeField(blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Enter a number between 0 and 100 for the discount percentage'
    )
    festive_discounts = models.BooleanField(default=False)
    festive_discount_description = models.TextField(blank=True, null=True)
    festive_discount_price = PositiveDecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    festive_discount_percentage = PositiveDecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.title

    # Discount decorator for Rental discounts
    def apply_discount(func):
        def wrapper(request, *args, **kwargs):
            item = func(request, *args, **kwargs)
            if item.discount_percentage > 0:
                discounted_price = item.price * (1 - item.discount_percentage / 100)
                item.discounted_price = discounted_price
            return item
        return wrapper

    # Discount strategy for Purchase discounts
    def calculate_festive_discount_price(self):
        strategies = [
            LabourDayDiscountStrategy, VesakDayDiscountStrategy,
            HariRayaHajiDiscountStrategy, TestDiscountStrategy,
        ]

        # Use undiscounted strategy as default
        discount_strategy = DefaultDiscountStrategy()

        # Iterate through strategies to check if activation_date matches today
        for strategy_class in strategies:
            if timezone.now().date() == strategy_class.activation_date:

                discount_strategy = strategy_class()
                break

        (self.festive_discount_description,
         self.festive_discount_percentage,
         self.festive_discount_price) = discount_strategy.calculate_discounted_deposit(self.deposit)

        self.save()

    def create_memento(self):
        """
        Create a memento object representing the current state of the Item.
        """
        return ItemMemento(
            item=self,
            owner=self.owner,
            title=self.title,
            description=self.description,
            category=self.category,
            condition=self.condition,
            availability=self.availability,
            price_per_day=self.price_per_day,
            deposit=self.deposit,
            image=self.image,
            created_date=self.created_date,
            deleted_date=self.deleted_date
        )

    def restore_from_memento(self, memento):
        """
        Restore the Item to a previous state using the provided memento.
        """
        self.owner = memento.owner
        self.title = memento.title
        self.description = memento.description
        self.category = memento.category
        self.condition = memento.condition
        self.availability = memento.availability
        self.price_per_day = memento.price_per_day
        self.deposit = memento.deposit
        self.image = memento.image
        self.created_date = memento.created_date
        self.deleted_date = memento.deleted_date
        self.save()

        # Delete the memento from the database
        # memento.delete()


class ItemMemento(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    condition = models.CharField(max_length=255, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')])
    availability = models.CharField(max_length=255, choices=[
        ('available', 'Available'), ('active_rental', 'Active Rental'), ('pending_purchase', 'Pending Purchase'), ('sold', 'Sold')
        ], default='available')
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='item_images/')
    created_date = models.DateTimeField()
    deleted_date = models.DateTimeField(blank=True, null=True)


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ItemStatesCaretaker(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='caretaker')
    memento = models.ForeignKey(ItemMemento, on_delete=models.CASCADE)
    datetime_saved = models.DateTimeField(default=timezone.now)

    def save_state(self):
        """
        Save the current state of the Item by creating a new memento.
        """
        memento = self.item.create_memento()
        memento.save()
        self.memento = memento

        ct1 = ItemStatesCaretaker(item=self.item, memento=memento)

        ct1.save()

    def restore_state(self):
        """
        Restore the Item to a previous state using the stored memento.
        """
        self.item.restore_from_memento(self.memento)

    def delete_state(self):
        self.delete


class Rental(models.Model):
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals_as_renter')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals_as_owner')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    pending_date = models.DateTimeField(blank=True, null=True)
    confirm_date = models.DateTimeField(blank=True, null=True)
    complete_date = models.DateTimeField(blank=True, null=True)
    cancelled_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=255,
        choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='pending'
        )
    apply_loyalty_discount = models.BooleanField(default=False, help_text='Apply loyalty discount for this rental')

    def __str__(self):
        return f'{self.item} ({self.owner}, {self.renter}): {self.start_date} - {self.end_date}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update(self)

    # Method that changes the state of the rental and triggers notifications
    def change_state(self, new_state):
        # Change the state of the rental

        if new_state == 'pending':
            self.pending_date = timezone.now()
        elif new_state == 'confirmed':
            self.confirm_date = timezone.now()
        elif new_state == 'completed':
            self.complete_date = timezone.now()
        elif new_state == 'cancelled':
            self.cancelled_date = timezone.now()

        self.status = new_state
        self.save()

        # Notify all observers
        self.notify_observers()


class Purchase(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases_as_renter')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases_as_owner')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    deal_date = models.DateField()
    deal_confirmed_date = models.DateTimeField(blank=True, null=True)
    deal_complete_date = models.DateTimeField(blank=True, null=True)
    deal_cancelled_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=255,
        choices=[('reserved', 'Reserved'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='reserved'
        )

    def __str__(self):
        return f'{self.item} ({self.owner}, {self.buyer}): {self.deal_date}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update(self)

    # Method that changes the state of the rental and triggers notifications
    def change_state(self, new_state):
        # Change the state of the rental
        if new_state == 'reserved':
            self.deal_date = timezone.now()
        elif new_state == 'confirmed':
            self.confirm_date = timezone.now()
        elif new_state == 'completed':
            self.deal_complete_date = timezone.now()
        elif new_state == 'cancelled':
            self.deal_cancelled_date = timezone.now()

        self.status = new_state
        self.save()

        # Notify all observers
        self.notify_observers()


# Define the Observer interface
class PurchaseObserver(ABC):
    @abstractmethod
    def update(self, rental):
        pass


# Implement concrete Observers (classes responsible for sending emails and messages)
class PurchaseEmailSender(PurchaseObserver):
    def update(self, purchase):
        # Logic to send email to the buyer or owner based on purchase state change
        purchase_message = "email sender received update from purchase "
        print(purchase_message + purchase.item.title + " " + purchase.status + " " + purchase.buyer.username + " " + purchase.owner.username)

        if purchase.status == 'reserved':
            subject = 'iRentStuff.app - You made a Purchase reservation'
            html_message = render_to_string('emails/purchase_added_email.html', {'purchase': purchase})
            send_email(subject, html_message, purchase.owner.email)

            subject2 = 'iRentStuff.app - You have a Purchase Offer'
            html_message2 = render_to_string('emails/purchase_added_email2.html', {'purchase': purchase})
            send_email(subject2, html_message2, purchase.buyer.email)

        elif purchase.status == 'confirmed':
            subject = 'iRentStuff.app - you have a Purchase Acceptance'
            html_message = render_to_string('emails/purchase_confirmed_email.html', {'purchase': purchase})
            send_email(subject, html_message, purchase.owner.email)

            subject2 = 'iRentStuff.app - You accepted a Purchase Offer'
            html_message2 = render_to_string('emails/purchase_confirmed_email2.html', {'purchase': purchase})
            send_email(subject2, html_message2, purchase.buyer.email)

        elif purchase.status == 'completed':
            subject = 'iRentStuff.app - you have completed a sale'
            html_message = render_to_string('emails/purchase_completed_email.html', {'purchase': purchase})
            send_email(subject, html_message, purchase.owner.email)

        elif purchase.status == 'cancelled':
            subject = 'iRentStuff.app - you have cancelled a purchase'
            html_message = render_to_string('emails/purchase_cancelled_email.html', {'purchase': purchase})
            send_email(subject, html_message, purchase.owner.email)


class PurchaseMessageSender(PurchaseObserver):
    def update(self, purchase):
        # Logic to send message to the buyer or owner based on purchase state change

        if purchase.status == 'reserved':
            message = Message()
            message.item = purchase.item
            message.enquiring_user = purchase.buyer
            message.sender = User.objects.get(id=1)
            message.recipient = purchase.buyer
            message.subject = 'Admin'
            message.content = 'Purchase has been reserved. Deal date is on ' + str(purchase.deal_date)
            message.timestamp = timezone.now()
            message.save()
        elif purchase.status == 'confirmed':
            message = Message()
            message.item = purchase.item
            message.enquiring_user = purchase.buyer
            message.sender = User.objects.get(id=1)
            message.recipient = purchase.owner
            message.subject = 'Admin'
            message.content = 'Purchase has been accepted. Deal date is on ' + str(purchase.deal_date)
            message.timestamp = timezone.now()
            message.save()
        elif purchase.status == 'completed':
            message = Message()
            message.item = purchase.item
            message.enquiring_user = purchase.buyer
            message.sender = User.objects.get(id=1)
            message.recipient = purchase.buyer
            message.subject = 'Admin'
            message.content = 'Purchase has been completed.'
            message.timestamp = timezone.now()
            message.save()
        elif purchase.status == 'cancelled':
            message = Message()
            message.item = purchase.item
            message.enquiring_user = purchase.buyer
            message.sender = User.objects.get(id=1)
            message.recipient = purchase.buyer
            message.subject = 'Admin'
            message.content = 'Purchase has been cancelled.'
            message.timestamp = timezone.now()
            message.save()


class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True)
    comment = models.TextField(blank=True)
    created_date = models.DateTimeField(blank=True)

    def __str__(self):
        return self.comment


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name='messages', on_delete=models.CASCADE)
    enquiring_user = models.ForeignKey(User, related_name='enquiring_messages', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.subject} - {self.sender} to {self.recipient} about {self.item.title} ({self.enquiring_user.username})'


class Interest(models.Model):
    categories = models.ManyToManyField(Category)
    created_date = models.DateTimeField(auto_now_add=True)
    discount = models.BooleanField(default=True)    # check if any discount available
    item_cd_crit = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(7)]) # item created date criteria, max past 7 days
    # deposit/buy cost as backup criteria

    def __str__(self):
        categories_name = ', '.join([category.name for category in self.categories.all()])
        return f' interested in {categories_name} and items created in the past {self.item_cd_crit} days.'


class UserInterests(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    interest = models.OneToOneField(Interest, on_delete=models.CASCADE)


# 3 template classes: Top3Categories, ItemMinDiscount, NewlyCreated (more can be created if need be)
class InterestDisplayTemplate:

    def get_items(self, interest):
        raise NotImplementedError("Subclasses must implement this method")


class Top3CategoryDisplay(InterestDisplayTemplate):
    def get_items(self, interest):
        categories = interest.categories.all()
        return Item.objects.filter(category__in=categories).order_by('category', 'title')


class ItemsDiscountDisplay(InterestDisplayTemplate):
    def get_items(self, interest):
        discount = interest.discount
        return Item.objects.filter(discount_percentage__gte=1).order_by('-discount_percentage')


class NewlyListedItemsDisplay(InterestDisplayTemplate):
    def get_items(self, interest):
        day_filter = interest.item_cd_crit if interest.item_cd_crit else 3
        return Item.objects.filter(created_date__gt=timezone.now() - timedelta(days=day_filter)).order_by('-created_date')
