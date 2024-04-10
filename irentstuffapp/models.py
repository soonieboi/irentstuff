from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import MinValueValidator
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from abc import ABC, abstractmethod
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives  

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
class Observer(ABC):
    @abstractmethod
    def update(self, rental):
        pass

# Implement concrete Observers (classes responsible for sending emails and messages)
class EmailSender(Observer):
    def update(self, rental):
        # Logic to send email to the renter or owner based on rental state change
        print("email sender received update from rental " + rental.item.title + " " + rental.status + " " + rental.renter.username + " " + rental.owner.username)

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
            html_message = render_to_string('emails/rental_completed_email.html', {'rental': rental,})
            send_email(subject, html_message, rental.owner.email)

        elif rental.status == 'cancelled': 
            subject = 'iRentStuff.app - you have cancelled a rental'
            html_message = render_to_string('emails/rental_cancelled_email.html', {'rental': rental,})
            send_email(subject, html_message, rental.owner.email)

class MessageSender(Observer):
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

#extend Decimal to prevent negative values
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

    def __str__(self):
        return self.title
    
    def apply_discount(func):
        def wrapper(request, *args, **kwargs):
            item = func(request, *args, **kwargs)
            if item.discount_percentage > 0:
                discounted_price = item.price * (1 - item.discount_percentage / 100)
                item.discounted_price = discounted_price
            return item
        return wrapper
    
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
        self.price_per_day = memento.price_per_day
        self.deposit = memento.deposit
        self.image = memento.image
        self.created_date = memento.created_date
        self.deleted_date = memento.deleted_date
        self.save()

        # Delete the memento from the database
        #memento.delete()

class ItemMemento(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    condition = models.CharField(max_length=255, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')])
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

        ct1 = ItemStatesCaretaker(item=self.item, memento = memento)

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
    status = models.CharField(max_length=255, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending')
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
