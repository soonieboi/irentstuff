from django import forms
from django.contrib.auth.models import User
from .models import Item, Rental, Message, Review, Purchase
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
        fields = ['title', 'image', 'description', 'category', 'condition',
                  'price_per_day', 'deposit', 'discount_percentage', 'festive_discounts']


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'image', 'description', 'category', 'condition',
                  'price_per_day', 'deposit', 'discount_percentage', 'festive_discounts']


class ItemReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rental', 'rating', 'comment']

    def __init__(self, user, item, *args, **kwargs):
        super(ItemReviewForm, self).__init__(*args, **kwargs)
        # Limit the rental choices to the ones belonging to the current user and current item
        print(f"item: {item}")
        self.fields['rental'].queryset = Rental.objects.filter(renter=user, item=item, status='completed')
        self.fields['rental'].label_from_instance = self.custom_label_from_instance

    def custom_label_from_instance(self, obj):
        return f'{obj.start_date} to {obj.end_date}'


class RentalForm(forms.ModelForm):

    renterid = forms.CharField(
        label="Renter (ID)",
        max_length=90,
        widget=forms.TextInput(attrs={'class': 'form-control autocomplete'}),
        required=True,
    )

    apply_loyalty_discount = forms.BooleanField(required=False, label="Apply 5% loyalty discount")

    class Meta:
        model = Rental
        fields = ['start_date', 'end_date', 'apply_loyalty_discount']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'item': forms.HiddenInput(),
            'owner': forms.HiddenInput(),
            'status': forms.HiddenInput(),
            'apply_loyalty_discount': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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


class PurchaseForm(forms.ModelForm):

    buyerid = forms.CharField(
        label="Buyer (ID)",
        max_length=90,
        widget=forms.TextInput(attrs={'class': 'form-control autocomplete'}),
        required=True,
    )

    class Meta:
        model = Purchase
        fields = ['deal_date']
        widgets = {
            'deal_date': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'item': forms.HiddenInput(),
            'owner': forms.HiddenInput(),
            'status': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        deal_date = cleaned_data.get('deal_date')

        if deal_date < timezone.now().date():
            raise forms.ValidationError('Start date cannot be earlier than today.')

        return cleaned_data


class MessageForm(forms.ModelForm):

    # Override the content field to use TextInput
    content = forms.CharField(label='', widget=forms.TextInput(attrs={'class': 'form-control border border-secondary'}))

    class Meta:
        model = Message
        fields = ['content']
