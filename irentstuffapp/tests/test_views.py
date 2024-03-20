from datetime import datetime, timezone
from django.test import TestCase, Client
from django.urls import reverse
from irentstuffapp.models import Item, Category, Message
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import mail


class InboxViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

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
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
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
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
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
        self.assertEqual(
            response.context["grouped_messages"][0]["item__title"], "Test Item 1"
        )
        self.assertEqual(
            response.context["grouped_messages"][1]["item__title"], "Test Item 2"
        )


class CheckUserExistsViewTestCase(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

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
        )  # follow=True allows to follow the redirect

        # Check if the user is redirected to the login page after successful registration
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[0], ("/login", 302))

        # Check if the user is created in the database
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

        # Check if the welcome email is sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "Welcome to iRentStuff.app - Your Account Registration is Successful!",
        )

        # Check if the success message is shown in the response
        self.assertContains(
            response, "Thank you for your registration! You may log in now"
        )

    def test_register_existing_user(self):
        # Create a user with the same email as in the test data
        User.objects.create_user(
            username="bobtan", email="test@example.com", password="password123"
        )

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
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

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
from datetime import datetime, timezone, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from irentstuffapp.models import Item, Category, Message, Rental
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core import mail
from irentstuffapp.views import cancel_rental
from django.core.exceptions import ValidationError
from django.utils import timezone

class InboxViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

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
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
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
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
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
        self.assertEqual(
            response.context["grouped_messages"][0]["item__title"], "Test Item 1"
        )
        self.assertEqual(
            response.context["grouped_messages"][1]["item__title"], "Test Item 2"
        )


class CheckUserExistsViewTestCase(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

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
        )  # follow=True allows to follow the redirect

        # Check if the user is redirected to the login page after successful registration
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[0], ("/login", 302))

        # Check if the user is created in the database
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

        # Check if the welcome email is sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "Welcome to iRentStuff.app - Your Account Registration is Successful!",
        )

        # Check if the success message is shown in the response
        self.assertContains(
            response, "Thank you for your registration! You may log in now"
        )

    def test_register_existing_user(self):
        # Create a user with the same email as in the test data
        User.objects.create_user(
            username="bobtan", email="test@example.com", password="password123"
        )

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
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

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


