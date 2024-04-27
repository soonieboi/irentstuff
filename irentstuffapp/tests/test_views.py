from datetime import datetime, timedelta, date
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpRequest
from django.test import TestCase, Client
from django.urls import reverse
from irentstuffapp.models import (Item, Category, Message, Rental, Purchase, Interest, UserInterests,
                                  InterestDisplayTemplate, Top3CategoryDisplay, ItemsDiscountDisplay, NewlyListedItemsDisplay)
from irentstuffapp.forms import ItemForm, ItemEditForm, RentalForm, PurchaseForm
from irentstuffapp.views import index
from PIL import Image
from unittest.mock import patch
from django.core.exceptions import ValidationError
import io
import os
import pytz

sgt = pytz.timezone('Asia/Singapore')


class InboxViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

    def test_inbox_authenticated(self):
        # Login as the user
        self.client.login(username="testuser", password="password123")

        # Create a test category to use in test items
        self.category = Category.objects.create(name="testcategory")

        # Create some test items
        self.item = Item.objects.create(
            owner=self.user,
            title="Test Item 1",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

        self.item2 = Item.objects.create(
            owner=self.user,
            title="Test Item 2",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

        # Create some sample messages
        Message.objects.create(
            sender=self.user,
            recipient=self.user,
            item=self.item,
            enquiring_user=self.user,
            subject="Test Subject1",
            content="Test Content1",
            is_read=False,
        )
        Message.objects.create(
            sender=self.user,
            recipient=self.user,
            item=self.item2,
            enquiring_user=self.user,
            subject="Test Subject2",
            content="Test Content2",
            is_read=False,
        )

        # Make a GET request to inbox view
        response = self.client.get(reverse("inbox"))

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Check that the correct template is used
        self.assertTemplateUsed(response, "irentstuffapp/inbox.html")

        # Check that the messages are grouped correctly
        self.assertEqual(len(response.context["grouped_messages"]), 2)
        self.assertEqual(response.context["grouped_messages"][0]["message_count"], 1)
        self.assertEqual(response.context["grouped_messages"][1]["message_count"], 1)
        self.assertEqual(response.context["grouped_messages"][0]["item__title"], "Test Item 1")
        self.assertEqual(response.context["grouped_messages"][1]["item__title"], "Test Item 2")


class CheckUserExistsViewTestCase(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_check_user_exists(self):
        # Initialize the client
        client = Client()

        # Make a GET request to the check_user_exists view with an existing username
        response_existing = client.get("/check_user_exists/testuser/")

        # Assert that the response status code is 200
        self.assertEqual(response_existing.status_code, 200)

        # Assert that the response is a JSON response
        self.assertIsInstance(response_existing, JsonResponse)

        # Assert that the JSON response contains the key 'exists' with value True
        self.assertTrue(response_existing.json()["exists"])

        # Make a GET request to the check_user_exists view with a non-existing username
        response_non_existing = client.get("/check_user_exists/nonexistinguser/")

        # Assert that the response status code is 200
        self.assertEqual(response_non_existing.status_code, 200)

        # Assert that the response is a JSON response
        self.assertIsInstance(response_non_existing, JsonResponse)

        # Assert that the JSON response contains the key 'exists' with value False
        self.assertFalse(response_non_existing.json()["exists"])


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_view(self):
        # Create a POST request with form data
        response = self.client.post(
            reverse("register"),
            {
                "email": "test@example.com",
                "password": "password123",
                "fname": "Bob",
                "lname": "Tan",
                "uname": "bobtan",
            },
            follow=True,
        )

        # Check if the user is redirected to the login page after successful registration
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[0], ("/login", 302))

        # Check if the user is created in the database
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

        # Check if the welcome email is sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Welcome to iRentStuff.app - Your Account Registration is Successful!")

        # Check if the success message is shown in the response
        self.assertContains(response, "Thank you for your registration! You may log in now")

    def test_register_existing_user(self):
        # Create a user with the same email as in the test data
        User.objects.create_user(username="bobtan", email="test@example.com", password="password123")

        # Create a POST request with form data
        response = self.client.post(
            reverse("register"),
            {
                "email": "test@example.com",
                "password": "password123",
                "fname": "Bob",
                "lname": "Tan",
                "uname": "bobtan",
            },
            follow=True,
        )

        # Check if the user is redirected back to the register page
        self.assertRedirects(response, reverse("register"))

        # Check if the warning message is shown in the response
        self.assertContains(response, "User with this email already exists")

        # Check if the user is not created in the database
        self.assertFalse(User.objects.filter(username="johndoe").exists())


class LoginUserViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

    def test_login_user_valid_credentials(self):
        # Create a POST request with valid credentials
        response = self.client.post(
            reverse("login"),
            {"uname": "testuser", "password": "password123"},
            follow=True,
        )

        # Check if the user is redirected to the home page after successful login
        self.assertRedirects(response, "/")

        # Check if the user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_user_invalid_credentials(self):
        # Create a POST request with invalid credentials
        response = self.client.post(
            reverse("login"),
            {"uname": "invaliduser", "password": "invalidpassword"},
            follow=True,
        )

        # Check if the user is redirected back to the login page
        self.assertRedirects(response, reverse("login"))

        # Check if the warning message is shown in the response
        self.assertContains(response, "Invalid Credentials")

        # Check if the user is not authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class LogoutUserViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

    def test_logout_user(self):
        # Log in the user
        self.client.login(username="testuser", password="password123")

        # Make a GET request to the logout_user view
        response = self.client.get(reverse("logout"))

        # Check that the user is redirected to the home page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")  # Assuming "/" is the URL for the home page

        # Check that the user is logged out
        self.assertNotIn("_auth_user_id", self.client.session)


class ItemsListViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create some test users
        self.thisuser = User.objects.create_user(username="thisuser", password="password123")
        self.thatuser = User.objects.create_user(username="thatuser", password="password456")

        # Create a test category to use in test items
        self.category = Category.objects.create(name="testcategory")

        # Create some test items
        self.item1 = Item.objects.create(
            owner=self.thisuser,
            title="Test Item 1",
            description="Test description 1",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )
        self.item2 = Item.objects.create(
            owner=self.thatuser,
            title="Test Item 2",
            description="Test description 2",
            category=self.category,
            condition="poor",
            price_per_day=50.00,
            deposit=250.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    # Test that the correct response is received and template is used without login
    def test_items_list(self):
        url = reverse("items_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "irentstuffapp/items.html")
        self.assertContains(response, "Test Item 1")
        self.assertContains(response, "Test Item 2")

    # Test that a logged in user sees the correct details in their items list view
    def test_items_list_authenticated(self):
        self.client.login(username="thisuser", password="password123")
        response = self.client.get(reverse("items_list_my"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "irentstuffapp/items.html")
        self.assertContains(response, "Test Item 1")
        self.assertNotContains(response, "Test Item 2")

    def test_items_list_search_query(self):
        # Make a GET request to the items_list view with a search query
        response = self.client.get(reverse("items_list_my") + "?search=Test Item 1")
        # Check that only item1 is displayed (matched the search query)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Item 1")
        self.assertNotContains(response, "Test Item 2")

    def test_items_list_category_filter(self):
        # Make a GET request to the items_list view with a search query
        response = self.client.get(reverse("items_list_my") + "?search=&category=testcategory")
        # Check that item 1 & item2 displayed (matched the search query)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Item 1")
        self.assertContains(response, "Test Item 2")


class AddItemViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.category = Category.objects.create(name="testcategory")

    def create_image(self, name="test_image.jpg", size=(1, 1), image_mode="RGB", image_format="JPEG"):
        image_data = io.BytesIO()
        image = Image.new(image_mode, size)
        image.save(image_data, format=image_format)
        image_data.seek(0)

        return ContentFile(image_data.getvalue(), name=name)

    def test_add_item_authenticated(self):
        # Login as the user
        self.client.login(username="testuser", password="password123")

        # Prepare form data
        form_data = {
            "title": "Test Item",
            "image": self.create_image(),  # Use the helper function to create a valid image file
            "description": "Test description",
            "category": self.category.id,
            "condition": "excellent",
            "price_per_day": 10.00,
            "deposit": 50.00,
            "discount_percentage": 10,
        }

        # Make a POST request to add_item view with form data
        response = self.client.post(reverse("add_item"), form_data, format="multipart")
        form = ItemForm(data=form_data, files={"image": self.create_image()})

        # Assert that the form is valid
        self.assertTrue(form.is_valid())

        # Check that the item was successfully added
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.count(), 1)  # Check that item was created
        self.assertEqual(Item.objects.first().owner, self.user)  # Check that item owner is correct
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": Item.objects.first().id}))

    def tearDown(self) -> None:
        # Get the path to the image file
        image_path = Item.objects.first().image.path

        # Check if the file exists and delete it
        if os.path.exists(image_path):
            os.remove(image_path)
        return super().tearDown()


class EditItemViewTestCase(TestCase):
    def create_image(self, name="test_image.jpg", size=(1, 1), image_mode="RGB", image_format="JPEG"):
        image_data = io.BytesIO()
        image = Image.new(image_mode, size)
        image.save(image_data, format=image_format)
        image_data.seek(0)

        return ContentFile(image_data.getvalue(), name=name)

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.category1 = Category.objects.create(name="testcategory1")
        self.category2 = Category.objects.create(name="testcategory2")
        self.image1 = self.create_image(name="test_image1.jpg")
        self.image2 = self.create_image(name="test_image2.jpg")
        self.item = Item.objects.create(
            owner=self.user,
            title="Test Item",
            description="Test description",
            category=self.category1,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            discount_percentage=0,
            image=self.image1,
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )
        self.image1_path = self.item.image.path

    def test_edit_item_authenticated_owner(self):
        # Login as the item owner
        self.client.login(username="testuser", password="password123")

        # Prepare form data for editing the item
        form_data = {
            "title": "Updated Test Item",
            "description": "Updated description",
            "category": self.category2.id,
            "condition": "good",
            "price_per_day": 20.00,
            "deposit": 100.00,
            "discount_percentage": 5,
            "image": self.image2,
        }

        # Make a POST request to edit_item view with form data
        response = self.client.post(
            reverse("edit_item", kwargs={"item_id": self.item.id}),
            form_data,
            follow=True,
        )

        form = ItemEditForm(data=form_data, files={"image": self.image2})

        # Assert that the form is valid
        self.assertTrue(f"Form is valid: {form.is_valid()}")

        # Check if the item was successfully edited
        self.assertEqual(response.status_code, 200)  # Check if redirected to item detail page
        self.item.refresh_from_db()  # Refresh the item from the database

        # Check if fields were updated
        self.assertEqual(self.item.title, "Updated Test Item")
        self.assertEqual(self.item.description, "Updated description")
        self.assertEqual(self.item.condition, "good")
        self.assertEqual(self.item.price_per_day, 20.00)
        self.assertEqual(self.item.deposit, 100.00)
        self.assertIn(self.image2.name.split(".")[0], self.item.image.name)

    def test_edit_item_not_authenticated_owner(self):
        self.notowner = User.objects.create_user(username="testuser2", email="test@example.com", password="password1234")
        # Login as the not item owner
        self.client.login(username="testuser2", password="password1234")

        response = self.client.get(
            reverse("edit_item", kwargs={"item_id": self.item.id}),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.item.title, "Test Item")

    def tearDown(self):
        # Get the paths to the image files
        image2_path = self.item.image.path

        # Check if the files exist and delete them
        if os.path.exists(image2_path):
            os.remove(image2_path)
        if os.path.exists(self.image1_path):
            os.remove(self.image1_path)


class DeleteItemViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.user,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_delete_item_authenticated(self):
        # Login as the user
        self.client.login(username="testuser", password="password123")

        # Get the initial count of items
        initial_item_count = Item.objects.count()

        # Make a POST request to delete_item view
        response = self.client.post(reverse("delete_item", kwargs={"item_id": self.item.id}), {'delete_confirm': 'confirmed'})

        # Check that the item was successfully deleted
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertEqual(Item.objects.count(), initial_item_count - 1)  # Check if item count is decreased
        self.assertIsNone(Item.objects.filter(pk=self.item.id).first())  # Check if item is deleted from database

    def test_delete_item_with_rental(self):
        self.renter = User.objects.create_user(username="testrenter", email="rent@example.com", password="password321")

        self.rental = Rental.objects.create(
            renter=self.renter,
            owner=self.user,
            item=self.item,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            status="confirmed",
        )
        # Login as the user
        self.client.login(username="testuser", password="password123")

        # Get the initial count of items
        initial_item_count = Item.objects.count()

        # Make a POST request to delete_item view
        response = self.client.post(reverse("delete_item", kwargs={"item_id": self.item.id}))

        # Check that the item was successfully deleted
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.count(), initial_item_count)  # Check if item count did not decrease
        self.assertIsNotNone(Item.objects.filter(pk=self.item.id).first())

    def test_delete_item_with_purchase(self):
        self.buyer = User.objects.create_user(username="testbuyer", email="buy@example.com", password="password321")

        self.purchase = Purchase.objects.create(
            buyer=self.buyer,
            owner=self.user,
            item=self.item,
            deal_date=date.today(),
            status="confirmed",
        )
        # Login as the owner
        self.client.login(username="testuser", password="password123")

        # Get the initial count of items
        initial_item_count = Item.objects.count()

        # Make a POST request to delete_item view
        response = self.client.post(reverse("delete_item", kwargs={"item_id": self.item.id}))

        # Check that the item was successfully deleted
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.count(), initial_item_count)  # Check if item count did not decrease
        self.assertIsNotNone(Item.objects.filter(pk=self.item.id).first())

    def test_delete_item_not_authenticated_owner(self):
        self.notowner = User.objects.create_user(username="testuser2", email="test@example.com", password="password1234")
        # Login as anyone else
        self.client.login(username="testuser2", password="password1234")

        initial_item_count = Item.objects.count()

        # Make a POST request to delete_item view
        response = self.client.post(reverse("delete_item", kwargs={"item_id": self.item.id}))

        # Check that the item was successfully deleted
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertEqual(Item.objects.count(), initial_item_count)  # Check if item count is decreased


class ItemDetailViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.user,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_item_detail_authenticated(self):
        # Login as the user
        self.client.login(username="testuser", password="password123")

        # Make a GET request to item_detail view
        response = self.client.get(reverse("item_detail", kwargs={"item_id": self.item.id}))

        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)

        # Check that the correct template is used
        self.assertTemplateUsed(response, "irentstuffapp/item_detail.html")

        # Check if the item is correctly passed to the template
        self.assertEqual(response.context["item"], self.item)


class AddRentalViewTestCase(TestCase):
    def create_image(self, name="test_image.jpg", size=(1, 1), image_mode="RGB", image_format="JPEG"):
        image_data = io.BytesIO()
        image = Image.new(image_mode, size)
        image.save(image_data, format=image_format)
        image_data.seek(0)

        return ContentFile(image_data.getvalue(), name=name)

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.renter = User.objects.create_user(username="testrenter", email="testrenter@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_add_rental_authenticated(self):
        # Login as the user
        self.client.login(username="testowner", password="password123")

        # Prepare form data
        form_data = {
            "start_date": datetime.today().date(),
            "end_date": datetime.today().date() + timedelta(days=7),
            "renterid": "testrenter",
        }

        form = RentalForm(data=form_data, files={"image": self.create_image()})

        # Assert that the form is valid
        self.assertTrue(form.is_valid())

        # Make a POST request to add_rental view with form data
        response = self.client.post(reverse("add_rental", kwargs={"item_id": self.item.pk}), form_data, follow=True)

        # Check that the rental was successfully added
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "irentstuffapp/item_detail.html")
        self.assertTrue(Rental.objects.filter(item=self.item).exists())
        rental = Rental.objects.get(item=self.item)
        self.assertEqual(rental.renter.username, "testrenter")
        self.assertEqual(rental.owner, self.owner)
        self.assertEqual(rental.status, "pending")

    def test_add_rental_not_item_owner(self):
        # Login as a different user (not the owner)
        self.client.login(username="testrenter", password="password456")

        # Make a POST request to add_rental view
        response = self.client.post(reverse("add_rental", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no rental was created
        self.assertFalse(Rental.objects.filter(item=self.item).exists())

    def test_add_rental_item_sold(self):
        # Mark the item as sold
        self.item.availability = 'sold'
        self.item.save()

        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Make a POST request to add_rental view
        response = self.client.post(reverse("add_rental", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no rental was created
        self.assertFalse(Rental.objects.filter(item=self.item).exists())

    def test_add_rental_active_rentals_exist(self):
        # Create an active rental for the item
        Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.item,
            start_date=datetime.today().date() - timedelta(days=5),
            end_date=datetime.today().date() + timedelta(days=5),
            status="pending"
        )

        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Make a POST request to add_rental view
        response = self.client.post(reverse("add_rental", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no rental was created and only 1 exists
        self.assertEqual(Rental.objects.filter(item=self.item).count(), 1)

    def test_add_rental_pending_purchases_exist(self):
        # Create a pending purchase for the item
        Purchase.objects.create(
            owner=self.owner,
            buyer=self.renter,
            item=self.item,
            deal_reserved_date=datetime.now(tz=sgt),
            deal_confirmed_date=datetime.now(tz=sgt),
            deal_complete_date=None,
            deal_cancelled_date=None,
            deal_date=datetime.today().date() + timedelta(1),
            status="reserved"
        )

        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Make a POST request to add_rental view
        response = self.client.post(reverse("add_rental", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no rental was created
        self.assertFalse(Rental.objects.filter(item=self.item).exists())

    def test_add_rental_renter_is_owner(self):
        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Prepare form data with the owner as the renter
        form_data = {
            "start_date": datetime.today().date(),
            "end_date": datetime.today().date() + timedelta(days=7),
            "renterid": "testowner",  # Owner as the renter
        }

        # Make a POST request to add_rental view with form data
        response = self.client.post(reverse("add_rental", kwargs={"item_id": self.item.pk}), form_data)

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no rental was created
        self.assertEqual(Rental.objects.filter(item=self.item).count(), 0)


class AcceptRentalViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.renter = User.objects.create_user(username="testrenter", email="testrenter@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_accept_rental(self):
        # Log in as the renter
        self.client.login(username="testrenter", password="password456")

        # Create a pending rental offer for the item
        Rental.objects.create(
            renter=self.renter,
            owner=self.owner,
            item=self.item,
            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="pending",
        )

        # Make a POST request to accept the rental offer
        response = self.client.post(reverse("accept_rental", kwargs={"item_id": self.item.id}), follow=True)

        # Check if the rental status is updated to 'confirmed'
        rental = Rental.objects.get(item=self.item)
        self.assertEqual(rental.status, "confirmed")

        # Check that there are 2 emails in the outbox
        self.assertEqual(len(mail.outbox), 2)

        # Check if the confirmation email is sent to the owner
        self.assertEqual(mail.outbox[0].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(mail.outbox[0].subject, "iRentStuff.app - you have a Rental Acceptance")

        # Check if the confirmation email is sent to the renter
        self.assertEqual(mail.outbox[1].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[1].to, [self.renter.email])
        self.assertEqual(mail.outbox[1].subject, "iRentStuff.app - You accepted a Rental Offer")

        # Check if the response redirects to the item detail page
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.id}))


class CompleteRentalViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.renter = User.objects.create_user(username="testrenter", email="testrenter@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_complete_rental(self):
        # Log in as the owner
        self.client.login(username="testowner", password="password123")

        # Create a confirmed rental for the item
        Rental.objects.create(
            renter=self.renter,
            owner=self.owner,
            item=self.item,
            start_date=datetime.now().date() - timedelta(2),
            end_date=datetime.now().date() - timedelta(1),
            status="confirmed",
        )

        # Make a POST request to complete the rental
        response = self.client.post(reverse("complete_rental", kwargs={"item_id": self.item.id}), follow=True)

        # Check if the rental status is updated to 'completed'
        rental = Rental.objects.get(item=self.item)
        self.assertEqual(rental.status, "completed")

        # Check that there is 1 email in the outbox
        self.assertEqual(len(mail.outbox), 1)

        # Check if the completion email is sent to the owner
        self.assertEqual(mail.outbox[0].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(mail.outbox[0].subject, "iRentStuff.app - you have set a rental to Complete")

        # Check if the response redirects to the item detail page
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.id}))


class CancelRentalViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username="testowner", email="testowner@example.com", password="password123"
        )
        self.renter = User.objects.create_user(
            username="testrenter",
            email="testrenter@example.com",
            password="password456",
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
            image="test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_cancel_rental(self):
        # Log in as the owner
        self.client.login(username="testowner", password="password123")

        # Create a pending rental for the item
        Rental.objects.create(
            renter=self.renter,
            owner=self.owner,
            item=self.item,
            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="pending",
        )

        # Make a POST request to cancel the rental
        response = self.client.post(
            reverse("cancel_rental", kwargs={"item_id": self.item.id}), follow=True
        )

        # Check if the rental status is updated to 'cancelled'
        rental = Rental.objects.get(item=self.item)
        self.assertEqual(rental.status, "cancelled")
        self.assertEqual(date.today(), rental.cancelled_date.date())

        # Check that there is 1 email in the outbox
        self.assertEqual(len(mail.outbox), 1)

        # Check if the cancellation email is sent to the owner
        self.assertEqual(mail.outbox[0].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(
            mail.outbox[0].subject, "iRentStuff.app - you have cancelled a rental"
        )

        # Check if the response redirects to the item detail page
        self.assertRedirects(
            response, reverse("item_detail", kwargs={"item_id": self.item.id})
        )


class AddPurchaseViewTestCase(TestCase):
    def create_image(self, name="test_image.jpg", size=(1, 1), image_mode="RGB", image_format="JPEG"):
        image_data = io.BytesIO()
        image = Image.new(image_mode, size)
        image.save(image_data, format=image_format)
        image_data.seek(0)

        return ContentFile(image_data.getvalue(), name=name)

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.buyer = User.objects.create_user(username="testbuyer", email="testbuyer@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_add_purchase_authenticated(self):
        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Prepare form data
        form_data = {
            "deal_date": datetime.today().date(),
            "buyerid": "testbuyer",
        }

        form = PurchaseForm(data=form_data, files={"image": self.create_image()})

        # Assert that the form is valid
        self.assertTrue(form.is_valid())

        # Make a POST request to add_purchase view with form data
        response = self.client.post(reverse("add_purchase", kwargs={"item_id": self.item.pk}), form_data, follow=True)

        # Check that the purchase was successfully added
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "irentstuffapp/item_detail.html")
        self.assertTrue(Purchase.objects.filter(item=self.item).exists())
        purchase = Purchase.objects.get(item=self.item)
        self.assertEqual(purchase.buyer.username, "testbuyer")
        self.assertEqual(purchase.owner, self.owner)
        self.assertEqual(purchase.status, "reserved")

    def test_add_purchase_not_item_owner(self):
        # Login as a different user (not the owner)
        self.client.login(username="testbuyer", password="password456")

        # Make a POST request to add_purchase view
        response = self.client.post(reverse("add_purchase", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no purchase was created
        self.assertFalse(Purchase.objects.filter(item=self.item).exists())

    def test_add_purchase_item_sold(self):
        # Mark the item as sold
        self.item.availability = 'sold'
        self.item.save()

        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Make a POST request to add_purchase view
        response = self.client.post(reverse("add_purchase", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no purchase was created
        self.assertFalse(Purchase.objects.filter(item=self.item).exists())

    def test_add_purchasel_active_rentals_exist(self):
        # Create an active rental for the item
        Rental.objects.create(
            owner=self.owner,
            renter=self.buyer,  # use buyer account to test for renter
            item=self.item,
            start_date=datetime.today().date() - timedelta(days=5),
            end_date=datetime.today().date() + timedelta(days=5),
            status="pending"
        )

        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Make a POST request to add_purchase view
        response = self.client.post(reverse("add_purchase", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no purchase was created
        self.assertFalse(Purchase.objects.filter(item=self.item).exists())

    def test_add_purchase_pending_purchases_exist(self):
        # Create a pending purchase for the item
        Purchase.objects.create(
            owner=self.owner,
            buyer=self.buyer,
            item=self.item,
            deal_reserved_date=datetime.now(tz=sgt),
            deal_confirmed_date=datetime.now(tz=sgt),
            deal_complete_date=None,
            deal_cancelled_date=None,
            deal_date=datetime.today().date() + timedelta(1),
            status="reserved"
        )

        # Login as the owner
        self.client.login(username="testowner", password="password123")

        # Make a POST request to add_purchase view
        response = self.client.post(reverse("add_purchase", kwargs={"item_id": self.item.pk}))

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no purchase was created
        self.assertEqual(Purchase.objects.filter(item=self.item).count(), 1)

    def test_add_purchase_buyer_is_owner(self):
        # Login as the owner
        self.client.login(username="testowner", password="password123")
        print(f"Purchase created start: {Purchase.objects.filter(item=self.item).count()}")

        # Prepare form data with the owner as the buyer
        form_data = {
            "deal_date": datetime.today().date(),
            "buyerid": "testowner",  # Owner as the buyer
        }

        # Make a POST request to add_purchase view with form data
        response = self.client.post(reverse("add_purchase", kwargs={"item_id": self.item.pk}), form_data)

        # Check that the user is redirected to the item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.pk}))

        # Check that no purchase was created
        print(f"Purchase created end: {Purchase.objects.filter(item=self.item).count()}")
        self.assertFalse(Purchase.objects.filter(item=self.item).count(), 0)


class AcceptPurchaseViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.buyer = User.objects.create_user(username="testbuyer", email="testbuyer@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_accept_purchase(self):
        # Log in as the buyer
        self.client.login(username="testbuyer", password="password456")

        # Create a pending purchase offer for the item
        Purchase.objects.create(
            buyer=self.buyer,
            owner=self.owner,
            item=self.item,
            deal_date=datetime.now().date() + timedelta(1),
            status="reserved",
        )

        # Make a POST request to accept the purchase offer
        response = self.client.post(reverse("accept_purchase", kwargs={"item_id": self.item.id}), follow=True)

        # Check if the purchase status is updated to 'confirmed'
        purchase = Purchase.objects.get(item=self.item)
        self.assertEqual(purchase.status, "confirmed")

        # Check that there are 2 emails in the outbox
        self.assertEqual(len(mail.outbox), 2)

        # Check if the confirmation email is sent to the owner
        self.assertEqual(mail.outbox[0].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(mail.outbox[0].subject, "iRentStuff.app - you have a Purchase Acceptance")

        # Check if the confirmation email is sent to the buyer
        self.assertEqual(mail.outbox[1].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[1].to, [self.buyer.email])
        self.assertEqual(mail.outbox[1].subject, "iRentStuff.app - You accepted a Purchase Offer")

        # Check if the response redirects to the item detail page
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.id}))


class CompletePurchaseViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.buyer = User.objects.create_user(username="testbuyer", email="testbuyer@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_complete_purchase(self):
        # Log in as the owner
        self.client.login(username="testowner", password="password123")

        # Create a confirmed purchase for the item
        Purchase.objects.create(
            buyer=self.buyer,
            owner=self.owner,
            item=self.item,
            deal_date=datetime.now().date() + timedelta(1),
            status="confirmed",
        )

        # Make a POST request to complete the purchase
        response = self.client.post(reverse("complete_purchase", kwargs={"item_id": self.item.id}), follow=True)

        # Check if the purchase status is updated to 'completed'
        purchase = Purchase.objects.get(item=self.item)
        self.assertEqual(purchase.status, "completed")

        # Check that there is 1 email in the outbox
        self.assertEqual(len(mail.outbox), 1)

        # Check if the completion email is sent to the owner
        self.assertEqual(mail.outbox[0].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(mail.outbox[0].subject, "iRentStuff.app - you have completed a sale")

        # Check if the response redirects to the item detail page
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.id}))


class CancelPurchaseViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.buyer = User.objects.create_user(username="testbuyer", email="testbuyer@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

    def test_cancel_purchase(self):
        # Log in as the owner
        self.client.login(username="testowner", password="password123")

        # Create a confirmed purchase for the item
        Purchase.objects.create(
            buyer=self.buyer,
            owner=self.owner,
            item=self.item,
            deal_date=datetime.now().date() + timedelta(1),
            status="reserved",
        )

        # Make a POST request to complete the purchase
        response = self.client.post(reverse("cancel_purchase", kwargs={"item_id": self.item.id}), follow=True)

        # Check if the purchase status is updated to 'completed'
        purchase = Purchase.objects.get(item=self.item)
        self.assertEqual(purchase.status, "cancelled")

        # Check that there is 1 email in the outbox
        self.assertEqual(len(mail.outbox), 1)

        # Check if the completion email is sent to the owner
        self.assertEqual(mail.outbox[0].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(mail.outbox[0].subject, "iRentStuff.app - you have cancelled a purchase")

        # Check if the response redirects to the item detail page
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.id}))


class AddReviewViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.renter = User.objects.create_user(username="testrenter", email="testrenter@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )
        self.rental = Rental.objects.create(
            renter=self.renter,
            owner=self.owner,
            item=self.item,
            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="completed",
        )

    def test_add_review(self):
        # Log in as the user
        self.client.login(username="testrenter", password="password456")

        # Make a POST request to add a review
        response = self.client.post(
            reverse("add_review", kwargs={"item_id": self.item.id}),
            {
                "rental": self.rental.id,
                "rating": 5,
                "comment": "Solid la!",
            },
            follow=True,
        )

        # Check if the review is added to the database and has the correct details
        self.assertEqual(self.rental.review_set.count(), 1)
        review = self.rental.review_set.first()
        self.assertEqual(review.comment, "Solid la!")
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.author, self.renter)

        # Check if the response redirects to the item detail page
        self.assertRedirects(response, reverse("item_detail", kwargs={"item_id": self.item.id}))

    def test_render_add_review_template(self):
        self.client.login(username="testowner", password="password123")
        response = self.client.get(reverse("add_review", kwargs={"item_id": self.item.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'irentstuffapp/review_add.html')


class ItemMessagesViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="testowner", email="testowner@example.com", password="password123")
        self.renter = User.objects.create_user(username="testrenter", email="testrenter@example.com", password="password456")
        self.category = Category.objects.create(name="testcategory")
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )
        self.message = Message.objects.create(
            sender=self.owner,
            recipient=self.renter,
            item=self.item,
            enquiring_user=self.renter,
            subject="Test Subject",
            content="Test Content",
            timestamp=datetime.now(),
            is_read=False,
        )

    def test_item_messages_owner_view(self):
        # Log in as the owner
        self.client.login(username="testowner", password="password123")

        # Make a GET request to the owner view of item messages
        response = self.client.get(
            reverse("item_messages", kwargs={"item_id": self.item.id, "userid": self.owner.id})
        )

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

    def test_item_messages_renter_view(self):
        # Log in as the owner
        self.client.login(username="testrenter", password="password456")

        # Make a GET request to the owner view of item messages
        response = self.client.get(
            reverse("item_messages", kwargs={"item_id": self.item.id, "userid": self.renter.id})
        )

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)


class CategoryInterestTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password123")
        self.category = Category.objects.create(name="testcategory")
        self.interest = Interest.objects.create(created_date=datetime.now(tz=sgt), discount=True, item_cd_crit=6)
        self.selected_categories = [self.category.id]

    def test_category_interest_post(self):
        # Log in as the owner
        self.client.login(username="testuser", password="password123")
        response = self.client.post(reverse("interest"), {
            'selected_categories': self.selected_categories,
            'item_cd_crit': 6
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        user_interests = UserInterests.objects.filter(user=self.user).first()
        self.assertIsNotNone(user_interests)

        interest = user_interests.interest
        self.assertIsNotNone(interest)

        self.assertTrue(interest.discount)
        self.assertEqual(interest.item_cd_crit, 6)
        categories = list(interest.categories.all().values_list('id', flat=True))
        self.assertListEqual(categories, [self.category.id,])

    def test_category_interest_get(self):
        response = self.client.get(reverse("interest"))
        self.assertEqual(response.status_code, 302)

    def test_existing_user_interest_redirect(self):
        self.client.login(username="testuser", password="password123")
        existing_user_interests = UserInterests.objects.create(user=self.user, interest=self.interest)

        response = self.client.post(reverse("interest"), {
            'selected_categories': self.selected_categories,
            'item_cd_crit': 3
        }, follow=True)
        self.assertRedirects(response, reverse('items_list'))

    def test_render_interest_template(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("interest"))
        self.assertTemplateUsed(response, 'irentstuffapp/interest.html')


class DiscountDisplayTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password123")
        self.category = Category.objects.create(name="testcategory")
        self.interest = Interest.objects.create(created_date=datetime.now(tz=sgt), discount=True, item_cd_crit=11)
        self.selected_categories = [self.category.id]
        self.item = Item.objects.create(
            owner=self.user,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
            discount_percentage=10
        )  # to fix tmr

    def test_deals_view(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse('deals'))
        self.assertEqual(response.status_code, 302)

    def test_deals_view_with_interest(self):
        self.client.login(username="testuser", password="password123")
        user_interests = UserInterests.objects.create(user=self.user, interest=self.interest)
        response = self.client.get(reverse('deals'), {'items': self.item}, follow=True)
        self.assertEqual(response.status_code, 200)


class NewItemsDisplayTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password123")
        self.category = Category.objects.create(name="testcategory")
        self.interest = Interest.objects.create(created_date=datetime.now(tz=sgt), discount=False, item_cd_crit=6)
        self.selected_categories = [self.category.id]

    def test_new_items_view(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse('new_items'))
        self.assertEqual(response.status_code, 302)

    def test_new_items_view_with_interest(self):
        self.client.login(username="testuser", password="password123")
        user_interests = UserInterests.objects.create(user=self.user, interest=self.interest)
        response = self.client.get(reverse('new_items'))
        self.assertEqual(response.status_code, 200)


class Top3DisplayTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="password123")
        self.category = Category.objects.create(name="testcategory") 
        self.category2 = Category.objects.create(name="testcategory2")
        self.category3 = Category.objects.create(name="testcategory3")
        self.interest = Interest.objects.create(created_date=datetime.now(tz=sgt), discount=False, item_cd_crit=8)
        self.selected_categories = [self.category.id, self.category2.id, self.category3.id]

    def test_fav_categories_view(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse('fav_categories'))
        self.assertEqual(response.status_code, 302)

    def test_fav_category_view_with_interest(self):
        self.client.login(username="testuser", password="password123")
        user_interests = UserInterests.objects.create(user=self.user, interest=self.interest)
        response = self.client.get(reverse('fav_categories'))
        self.assertEqual(response.status_code, 200)


class IndexViewTestCase(TestCase):
    def test_index_view(self):

        request = HttpRequest()
        response = index(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Index")
