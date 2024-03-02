from django import forms
from django.contrib.auth.models import User
from .models import Item, Rental, Message
from django.utils import timezone 
from django.contrib.auth.forms import UserChangeForm

class NameChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)
    # Add validation logic as needed


class ItemEditForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'image', 'description', 'category', 'condition', 'price_per_day', 'deposit']

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'image', 'description', 'category', 'condition', 'price_per_day', 'deposit']

class RentalForm(forms.ModelForm):

    renterid = forms.CharField(
        label="Renter (ID)",
        max_length=90,
        widget=forms.TextInput(attrs={'class': 'autocomplete'}),
        required=True,
    )

    class Meta:
        model = Rental
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'datepicker'}),
            'end_date': forms.DateInput(attrs={'class': 'datepicker'}),
            'item': forms.HiddenInput(),
            'owner': forms.HiddenInput(),
            'status': forms.HiddenInput()
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date < timezone.now().date():
            raise forms.ValidationError('Start date cannot be earlier than today.')

        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError('End date must be later than the start date.')

        return cleaned_data

class MessageForm(forms.ModelForm):

    # Override the content field to use TextInput
    content = forms.CharField(label='', widget=forms.TextInput(attrs={'class': 'form-control border border-secondary'}))

    class Meta:
        model = Message
        fields = ['content']

