from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


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


    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

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
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True)
    # You can add additional fields like rating, payment details, etc.

    def __str__(self):
        return f'{self.item} ({self.owner}, {self.renter}): {self.start_date} - {self.end_date}'

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
        