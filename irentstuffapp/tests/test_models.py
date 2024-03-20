from datetime import datetime, timedelta, timezone
from django.contrib.auth.models import User
from django.test import TestCase
from irentstuffapp.models import Item, Category, Rental, Review, Message


class CategoryModelTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="testcategory")

    def test_category_creation(self):
        """Test that Category instance was created correctly"""
        # Retrieve the created Category from the database
        category = self.category

        # Assert that the category was created with the correct name
        self.assertEquals(category.name, "testcategory")

        # Assert that the category was created with the correct type
        self.assertEquals(str(category), "testcategory")


class ItemModelTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="testpassword1"
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
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            deleted_date=None,
        )

    def test_item_creation(self):
        """Test that Item instance was created correctly"""
        # Retrieve the created Item from the database
        item = self.item

        # Assert that the item was created successfully
        self.assertIsNotNone(item)

        # Assert that the attributes of the item are correct
        self.assertEquals(item.owner, self.owner)
        self.assertEquals(item.title, "Test Item")
        self.assertEquals(item.description, "Test description")
        self.assertEquals(item.category, self.category)
        self.assertEquals(item.condition, "excellent")
        self.assertEquals(item.price_per_day, 10.00)
        self.assertEquals(item.deposit, 50.00)
        self.assertEquals(item.image, "item_images/test_image.jpg")
        self.assertIsNotNone(item.created_date)
        self.assertIsNone(item.deleted_date)


class RentalModelTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="testpassword1"
        )
        self.renter = User.objects.create_user(
            username="renter", password="testpassword2"
        )
        self.enquiring_user = User.objects.create_user(
            username="enquirer", password="testpassword3"
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
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            deleted_date=None,
        )

        self.rental = Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.item,
            start_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            end_date=(
                datetime(2024, 2, 7, tzinfo=timezone.utc) + timedelta(days=7)
            ).date(),
            pending_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            confirm_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            complete_date=None,
            cancelled_date=None,
            status="confirmed",
        )

    def test_rental_creation(self):
        """Test that Rental instance was created correctly"""
        # Retrieve the rental from the database
        rental = self.rental

        # Assert that the rental was created successfully
        self.assertIsNotNone(rental)

        # Assert that the attributes of the rental are correct
        self.assertEquals(rental.owner, self.owner)
        self.assertEquals(rental.renter, self.renter)
        self.assertEquals(rental.item, self.item)
        self.assertEquals(rental.start_date, datetime(2024, 2, 7, tzinfo=timezone.utc))
        self.assertEquals(
            rental.end_date,
            (datetime(2024, 2, 7, tzinfo=timezone.utc) + timedelta(days=7)).date(),
        )
        self.assertEquals(
            rental.pending_date, datetime(2024, 2, 7, tzinfo=timezone.utc)
        )
        self.assertEquals(
            rental.confirm_date, datetime(2024, 2, 7, tzinfo=timezone.utc)
        )
        self.assertIsNone(rental.complete_date)
        self.assertIsNone(rental.cancelled_date)
        self.assertEquals(rental.status, "confirmed")


class ReviewModelTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="testpassword1"
        )
        self.renter = User.objects.create_user(
            username="renter", password="testpassword2"
        )
        self.enquiring_user = User.objects.create_user(
            username="enquirer", password="testpassword3"
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
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            deleted_date=None,
        )

        self.rental = Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.item,
            start_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            end_date=(
                datetime(2024, 2, 7, tzinfo=timezone.utc) + timedelta(days=7)
            ).date(),
            pending_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            confirm_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            complete_date=None,
            cancelled_date=None,
            status="confirmed",
        )

        self.review = Review.objects.create(
            author=self.owner,
            rental=self.rental,
            rating=5,
            comment="Test comment",
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
        )

    def test_review_creation(self):
        """Test that Review instance was created correctly"""
        # Retrieve the review from the database
        review = self.review

        # Assert that the review was created successfully
        self.assertIsNotNone(review)

        # Assert that the attributes of the review are correct
        self.assertEquals(review.author, self.owner)
        self.assertEquals(review.rental, self.rental)
        self.assertEquals(review.rating, 5)
        self.assertEquals(review.comment, "Test comment")
        self.assertIsNotNone(review.created_date)


class MessageModelTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.owner = User.objects.create_user(
            username="owner", password="testpassword1"
        )
        self.renter = User.objects.create_user(
            username="renter", password="testpassword2"
        )
        self.enquiring_user = User.objects.create_user(
            username="enquirer", password="testpassword3"
        )

        # Create a category
        self.category = Category.objects.create(name="testcategory")

        # Create an Item instance
        self.item = Item.objects.create(
            owner=self.owner,
            title="Test Item",
            description="Test description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            deleted_date=None,
        )

        # Create a Message instance
        self.message = Message.objects.create(
            sender=self.renter,
            recipient=self.owner,
            item=self.item,
            enquiring_user=self.enquiring_user,
            subject="Test Message Subject",
            content="Test Message Content",
        )

    def test_message_creation(self):
        """Test that Message instance was created correctly"""
        # Retrieve the message from the database
        message = self.message

        # Assert that the message was created successfully
        self.assertIsNotNone(message)

        # Assert that the attributes of the message are correct
        self.assertEquals(message.sender, self.renter)
        self.assertEquals(message.recipient, self.owner)
        self.assertEquals(message.item, self.item)
        self.assertEquals(message.enquiring_user, self.enquiring_user)
        self.assertEquals(message.subject, "Test Message Subject")
        self.assertEquals(message.content, "Test Message Content")
        self.assertFalse(message.is_read)
