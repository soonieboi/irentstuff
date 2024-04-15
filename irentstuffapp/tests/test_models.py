from datetime import datetime, timedelta, timezone
from django.contrib.auth.models import User
from django.test import TestCase
from django.core import mail
from irentstuffapp.models import Item, Category, Rental, Review, Message, ItemStatesCaretaker, EmailSender, MessageSender, Interest, UserInterests
from irentstuffapp.models import Top3CategoryDisplay, ItemsDiscountDisplay, NewlyListedItemsDisplay


class ObserverPatternTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="testpassword1", email="owner@test.com"
        )
        self.renter = User.objects.create_user(
            username="renter", password="testpassword2", email="user@test.com"
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
            
            pending_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            confirm_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            complete_date=None,
            cancelled_date=None,

            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="pending",
        )

    def test_rental_state_change(self):

        # Add observers
        email_sender = EmailSender()
        message_sender = MessageSender()
        self.rental.add_observer(email_sender)
        self.rental.add_observer(message_sender)

        # Change rental state to 'confirmed'
        self.rental.change_state('confirmed')

        self.rental.refresh_from_db()

        self.assertEqual(self.rental.status, "confirmed") 

        # Check if email are sent
        self.assertEqual(len(mail.outbox), 2)  # Check if two emails were sent

        # Check if the confirmation email is sent to the owner
        self.assertEqual(mail.outbox[0].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(mail.outbox[0].subject, "iRentStuff.app - you have a Rental Acceptance")

        # Check if the confirmation email is sent to the renter
        self.assertEqual(mail.outbox[1].from_email, "admin@irentstuff.app")
        self.assertEqual(mail.outbox[1].to, [self.renter.email])
        self.assertEqual(mail.outbox[1].subject, "iRentStuff.app - You accepted a Rental Offer")

        # Check if message was sent
        self.assertEqual(len(Message.objects.all()), 1)  # Check if message was sent
        self.assertEqual(Message.objects.first().id, 1) # message is sent by admin, id is 1
        self.assertEqual(Message.objects.first().subject, 'Admin')
        self.assertIn('Rental has been accepted. Period of rental is from ', Message.objects.first().content)

#tests ItemStatesCaretaker and ItemMemento models (ItemMemento is instantiated in Item class)
class MementoPatternTestCase(TestCase):
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
        item = self.item
        caretaker = ItemStatesCaretaker.objects.filter(item=item).first()
        if not caretaker:
            caretaker = ItemStatesCaretaker(item=item)

        caretaker.save_state()

    def test_create_and_restore_state(self):
        initial_state = {
            'owner': self.item.owner,
            'title': self.item.title,
            'description': self.item.description,
            'category': self.item.category,
            'condition': self.item.condition,
            'price_per_day': self.item.price_per_day,
            'deposit': self.item.deposit,
            'image': self.item.image,
            'created_date': self.item.created_date,
            'deleted_date': self.item.deleted_date
        }
        # Change item state
        self.item.title = 'Updated Title'
        self.item.description = 'Updated Description'
        self.item.save()
        self.item.refresh_from_db()

        caretaker = ItemStatesCaretaker.objects.filter(item=self.item).first()
        if not caretaker:
            caretaker = ItemStatesCaretaker(item=self.item)
        caretaker.save_state()

        # Restore from caretaker
        caretakerdel = ItemStatesCaretaker.objects.filter(item=self.item).order_by('-datetime_saved').first()
        if caretakerdel:
            caretakerdel.delete()

        caretaker = ItemStatesCaretaker.objects.filter(item=self.item).order_by('-datetime_saved').first()
        caretaker.restore_state()  # Restore the item to the previous state

        self.item.refresh_from_db()

        self.assertEqual(self.item.title, initial_state['title'])



class CategoryModelTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="testcategory")

    def test_category_creation(self):
        """Test that Category instance was created correctly"""
        # Retrieve the created Category from the database
        category = self.category

        # Assert that the category was created with the correct name
        self. assertEqual(category.name, "testcategory")

        # Assert that the category was created with the correct type
        self. assertEqual(str(category), "testcategory")


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
        self. assertEqual(item.owner, self.owner)
        self. assertEqual(item.title, "Test Item")
        self. assertEqual(item.description, "Test description")
        self. assertEqual(item.category, self.category)
        self. assertEqual(item.condition, "excellent")
        self. assertEqual(item.price_per_day, 10.00)
        self. assertEqual(item.deposit, 50.00)
        self. assertEqual(item.image, "item_images/test_image.jpg")
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
        self. assertEqual(rental.owner, self.owner)
        self. assertEqual(rental.renter, self.renter)
        self. assertEqual(rental.item, self.item)
        self. assertEqual(rental.start_date, datetime(2024, 2, 7, tzinfo=timezone.utc))
        self. assertEqual(
            rental.end_date,
            (datetime(2024, 2, 7, tzinfo=timezone.utc) + timedelta(days=7)).date(),
        )
        self. assertEqual(
            rental.pending_date, datetime(2024, 2, 7, tzinfo=timezone.utc)
        )
        self. assertEqual(
            rental.confirm_date, datetime(2024, 2, 7, tzinfo=timezone.utc)
        )
        self.assertIsNone(rental.complete_date)
        self.assertIsNone(rental.cancelled_date)
        self. assertEqual(rental.status, "confirmed")
        self. assertEqual(str(rental), f'{self.item} ({self.owner}, {self.renter}): {self.rental.start_date} - {self.rental.end_date}')


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
            start_date=datetime(2024, 2, 7, tzinfo=timezone.utc).date(),
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
        self. assertEqual(review.author, self.owner)
        self. assertEqual(review.rental, self.rental)
        self. assertEqual(review.rating, 5)
        self. assertEqual(review.comment, "Test comment")
        self.assertIsNotNone(review.created_date)
        self. assertEqual(str(review), "Test comment")


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
        self. assertEqual(message.sender, self.renter)
        self. assertEqual(message.recipient, self.owner)
        self. assertEqual(message.item, self.item)
        self. assertEqual(message.enquiring_user, self.enquiring_user)
        self. assertEqual(message.subject, "Test Message Subject")
        self. assertEqual(message.content, "Test Message Content")
        self.assertFalse(message.is_read)
        self. assertEqual(str(message),
            "Test Message Subject - renter to owner about Test Item (enquirer)",
        )

class InterestModelTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics')

    def test_interest_model_str(self):
        interest = Interest.objects.create(item_cd_crit=5)
        interest.categories.add(self.category)

        expected_str = f' interested in {self.category.name} and items created in the past 5 days.'
        self.assertEqual(str(interest), expected_str)

class UserInterestsModelTestCase(TestCase):
    def setUp(self):

        self.user = User.objects.create_user(username='testuser', password='test123')
        category_1 = Category.objects.create(name='Garden')
        category_2 = Category.objects.create(name='Games')
        category_3 = Category.objects.create(name='Toys')

        # Create an Interest object for testing
        self.interest = Interest.objects.create(item_cd_crit=6)
        self.interest.categories.add(category_1, category_2, category_3)

    def test_user_interests_model(self):
        # Create a UserInterests object for testing
        user_interests = UserInterests.objects.create(user=self.user, interest=self.interest)

        # Check if the user and interest are correctly associated
        self.assertEqual(user_interests.user, self.user)
        self.assertEqual(user_interests.interest, self.interest)

class DisplayTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.category1 = Category.objects.create(name='Category 1')
        self.category2 = Category.objects.create(name='Category 2')
        self.item1 = Item.objects.create(title='Item 1', category=self.category1, price_per_day=10.00, discount_percentage=0, deposit = 100.00, owner=self.user,
                                         created_date= datetime.now(tz=timezone.utc) - timedelta(days=2), image='item_images/test_image.jpg')
        self.item2 = Item.objects.create(title='Item 2', category=self.category2, price_per_day=20.00, discount_percentage=5, deposit = 100.00, owner=self.user, 
                                        created_date= datetime.now(tz=timezone.utc) - timedelta(days=10), image='item_images/test_image.jpg')
        self.interest = Interest.objects.create()
        self.interest.categories.add(self.category1, self.category2)
        self.user_interests = UserInterests.objects.create(user=self.user, interest=self.interest)

    def test_top3_category_display(self):
        display = Top3CategoryDisplay()
        items = display.get_items(self.interest)
        self.assertEqual(len(items), 2)

    def test_items_discount_display(self):
        display = ItemsDiscountDisplay()
        items = display.get_items(self.interest)
        self.assertEqual(len(items), 1)  

    def test_newly_listed_items_display(self):
        display = NewlyListedItemsDisplay()
        items = display.get_items(self.interest)
        self.assertEqual(len(items), 1)  

    def test_top3_category_display_ordering(self):
        display = Top3CategoryDisplay()
        items = display.get_items(self.interest)
        self.assertEqual(items.first(), self.item1)  

    def test_newly_listed_items_display_time_filter(self):
        self.item1.created_date = datetime.now(tz=timezone.utc) - timedelta(days=2)
        self.item1.save()
        self.item2.created_date = datetime.now(tz=timezone.utc) - timedelta(days=7)
        self.item2.save()
        display = NewlyListedItemsDisplay()
        items = display.get_items(self.interest)
        self.assertEqual(len(items), 1)  