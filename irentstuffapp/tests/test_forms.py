from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase
from irentstuffapp.forms import (
    NameChangeForm,
    PasswordChangeForm,
    ItemEditForm,
    ItemForm,
    ItemReviewForm,
    RentalForm,
    PurchaseForm,
    MessageForm,
    InterestForm,
)
from irentstuffapp.models import Item, Category, Rental, Purchase, Interest, UserInterests
from PIL import Image
import io
import pytz

sgt = pytz.timezone('Asia/Singapore')


class NameChangeFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
            first_name="Ah Kow",
            last_name="Tan",
        )

    def test_valid_form(self):
        form_data = {"first_name": "Mati", "last_name": "Lim"}
        form = NameChangeForm(instance=self.user, data=form_data)
        self.assertTrue(form.is_valid())


class PasswordChangeFormTestCase(TestCase):

    def test_valid_form(self):
        user = User.objects.create_user(username="testuser", password="oldpassword")
        form_data = {
            "old_password": user.password,  # Valid old password
            "new_password1": "newpassword",  # Valid new password
            "new_password2": "newpassword",  # Matching confirmation password
        }
        form = PasswordChangeForm(data=form_data)
        self.assertTrue(
            form.is_valid(),
            f"Form is unexpectedly invalid. Errors: {form.errors.as_data()}",
        )


class ItemEditFormTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.user,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_valid_form(self):
        form_data = {
            "title": "Updated Test Item",  # Valid updated title
            "description": "Updated description",  # Valid updated description
            "category": self.category,  # Valid updated category
            "condition": "good",  # Valid updated condition
            "price_per_day": 15.00,  # Valid updated price_per_day
            "deposit": 100.00,  # Valid updated deposit
            "discount_percentage": 10,
        }
        form = ItemEditForm(data=form_data, instance=self.item)
        self.assertTrue(
            form.is_valid(),
            f"Form is unexpectedly invalid. Errors: {form.errors.as_data()}",
        )


class ItemFormTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")

    def create_image(
        self,
        name="test_image.jpg",
        size=(1, 1),
        image_mode="RGB",
        image_format="JPEG",
    ):
        image_data = io.BytesIO()
        image = Image.new(image_mode, size)
        image.save(image_data, format=image_format)
        image_data.seek(0)

        return ContentFile(image_data.getvalue(), name=name)

    def test_valid_form(self):
        # Prepare form data
        form_data = {
            "title": "Test Item",
            "image": self.create_image(),  # Use the helper function to create a valid image file
            "description": "Test description",
            "category": self.category.id,
            "condition": "excellent",
            "price_per_day": 10.00,
            "deposit": 50.00,
            "discount_percentage": 5,
        }

        # Create form instance with form data
        form = ItemForm(data=form_data, files={"image": form_data["image"]})

        # Check if the form is valid
        self.assertTrue(form.is_valid(), form.errors.as_data())


class ItemReviewFormTestCase(TestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        # Create a test item
        self.item = Item.objects.create(
            owner=self.user,
            title="Test Item",
            description="Test description",
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
        )

        # Create a test rental
        self.rental = Rental.objects.create(
            item=self.item,
            owner=self.user,
            renter=self.user,
            start_date=datetime(2024, 2, 10, tzinfo=sgt),
            end_date=datetime(2024, 2, 15, tzinfo=sgt),
            status="completed",
        )

    def test_valid_form(self):
        # Create form data
        form_data = {
            "rental": self.rental.id,
            "rating": 5,
            "comment": "Great experience with this item!",
        }

        # Create form instance
        form = ItemReviewForm(user=self.user, item=self.item, data=form_data)

        # Check if form is valid
        self.assertTrue(form.is_valid())
        # Check custom_label_from_instance method
        self.assertEquals(form.custom_label_from_instance(self.rental), f'{self.rental.start_date} to {self.rental.end_date}')

    def test_invalid_form(self):
        # Create form data with invalid rental ID
        invalid_rental_id = 9999
        form_data = {
            "rental": invalid_rental_id,
            "rating": 5,
            "comment": "Great experience with this item!",
        }

        # Create form instance
        form = ItemReviewForm(user=self.user, item=self.item, data=form_data)

        # Check if form is invalid
        self.assertFalse(form.is_valid())

        # Check if rental field has error message
        self.assertTrue("rental" in form.errors)


class RentalFormTestCase(TestCase):

    def create_image(
        self,
        name="test_image.jpg",
        size=(1, 1),
        image_mode="RGB",
        image_format="JPEG",
    ):
        image_data = io.BytesIO()
        image = Image.new(image_mode, size)
        image.save(image_data, format=image_format)
        image_data.seek(0)

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        # Create a test item
        self.item = Item.objects.create(
            owner=self.user,
            image=self.create_image(),
            title="Test Item",
            description="Test description",
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
        )

    def test_valid_form(self):
        # Create form data
        form_data = {
            "renterid": str(self.user.id),
            "start_date": datetime.now().date() + timedelta(days=1),
            "end_date": datetime.now().date() + timedelta(days=5),
        }

        # Create form instance
        form = RentalForm(data=form_data)

        # Check if form is valid
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        # Create form data with invalid start date (earlier than today)
        form_data = {
            "renterid": str(self.user.id),
            "start_date": datetime.now().date() - timedelta(days=2),
            "end_date": datetime.now().date() + timedelta(days=5),
        }

        # Create form instance
        form = RentalForm(data=form_data)

        # Check if form is invalid
        self.assertFalse(form.is_valid())

        # Check if 'start_date' field has error message
        self.assertTrue(
            "Start date cannot be earlier than today." in form.errors.get("__all__")
        )

        # Create form data with end date earlier than start date
        form_data = {
            "renterid": str(self.user.id),
            "start_date": datetime.now().date() + timedelta(days=5),
            "end_date": datetime.now().date() + timedelta(days=1),
        }

        # Create form instance
        form = RentalForm(data=form_data)

        # Check if form is invalid
        self.assertFalse(form.is_valid())

        # Check if 'end_date' field has error message
        self.assertTrue(
            "End date must be later than the start date." in form.errors.get("__all__")
        )


class PurchaseFormTestCase(TestCase):

    def create_image(
        self,
        name="test_image.jpg",
        size=(1, 1),
        image_mode="RGB",
        image_format="JPEG",
    ):
        image_data = io.BytesIO()
        image = Image.new(image_mode, size)
        image.save(image_data, format=image_format)
        image_data.seek(0)

    def setUp(self):
        # Create test users
        self.owner = User.objects.create_user(
            username="testowner", email="testowner@example.com", password="password123"
        )
        self.buyer = User.objects.create_user(
            username="testbuyer", email="testbuyer@example.com", password="password456"
        )

        # Create a test item
        self.item = Item.objects.create(
            owner=self.owner,
            image=self.create_image(),
            title="Test Item",
            description="Test description",
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
        )

    def test_valid_form(self):
        # Create form data
        form_data = {
            "buyerid": str(self.buyer.id),
            "deal_date": datetime.now().date() + timedelta(days=1),
        }

        # Create form instance
        form = PurchaseForm(data=form_data)

        # Check if form is valid
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        # Create form data with invalid start date (earlier than today)
        form_data = {
            "buyerid": str(self.buyer.id),
            "deal_date": datetime.now().date() - timedelta(days=2),
        }

        # Create form instance
        form = PurchaseForm(data=form_data)

        # Check if form is invalid
        self.assertFalse(form.is_valid())

        # Check if 'start_date' field has error message
        self.assertTrue(
            "Purchase date cannot be earlier than today." in form.errors.get("__all__")
        )


class MessageFormTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.enquiring_user = User.objects.create_user(
            username="enquiring_user", password="password123"
        )

        self.category = Category.objects.create(name="testcategory")

        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_valid_form(self):
        # Prepare form data
        form_data = {
            "sender": self.enquiring_user,  # Provide the sender ID
            "recipient": self.owner,  # Provide the recipient ID
            "item": self.item,  # Provide the item ID
            "enquiring_user": self.enquiring_user,  # Provide the enquiring user ID
            "subject": "Test Subject",
            "content": "Test message content",
            "timestamp": datetime.now(),  # Provide the timestamp (if necessary)
            "is_read": False,  # Set the is_read field
        }

        # Instantiate the form with form data
        form = MessageForm(data=form_data)

        # Check if the form is valid
        self.assertTrue(form.is_valid())


class InterestFormTestCase(TestCase):
    def setUp(self):
        self.interest = Interest.objects.create(
            discount=True,
            item_cd_crit=6,
            created_date=datetime.now(),
        )
        self.interest.categories.set([Category.objects.create(name='Garden'),
                                      Category.objects.create(name='Toys'),
                                      Category.objects.create(name='Electronics')])

    def test_valid_form(self):
        # Prepare form data
        form_data = {
            "categories": [Category.objects.create(name='Garden'), Category.objects.create(name='Toys'), Category.objects.create(name='Electronics')],
            "discount": True,
            "item_cd_crit": 6,
            "created_date": datetime.now()
        }

        # Instantiate the form with form data
        form = InterestForm(instance=self.interest, data=form_data)

        # Check if the form is valid
        self.assertTrue(form.is_valid())
