from datetime import datetime, timedelta, timezone
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.core import mail
from django.urls import reverse
from irentstuffapp.models import Item, Category, Rental, Review, Message, ItemStatesCaretaker, EmailSender, MessageSender
from irentstuffapp.states import ItemState, ConcreteRentalCompleted, ConcreteRentalPending, ConcreteRentalOngoing, ConcreteUserIsItemOwner, ConcreteUserIsNotItemOwner

import logging

logging.basicConfig(level=logging.DEBUG)

# owner actions
## owner can cancel rental if rental is not accepted yet (rental status: pending)
## owner can complete rental if rental is accepted (rental status: confirmed)
## owner can add rental if there are no active rental
## owner can edit/ delete item if there are no active rental

# renter actions
## renter can accept rental if rental date has not started (rental status: pending) 

class ItemStateTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(
            username="owner", password="testpassword1", email="owner@test.com"
        )
        self.owner2 = User.objects.create_user(
            username="owner2", password="testpassword2", email="owner2@test.com"
        )
        self.renter = User.objects.create_user(
            username="renter", password="testpassword1", email="user@test.com"
        )
        self.renter2 = User.objects.create_user(
            username="renter2", password="testpassword2", email="user2@test.com"
        )

        self.category = Category.objects.create(name="testcategory")

        self.items = [
            Item.objects.create(
                owner=self.owner,
                title="State Test Item",
                description="Test description",
                category=self.category,
                condition="excellent",
                price_per_day=10.00,
                deposit=50.00,
                image="item_images/test_image.jpg",
                created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
                deleted_date=None,
            ),
            Item.objects.create(
                owner=self.owner2,
                title="State Test Item 2",
                description="Test description",
                category=self.category,
                condition="excellent",
                price_per_day=10.00,
                deposit=50.00,
                image="item_images/test_image.jpg",
                created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
                deleted_date=None,
            )
        ]

        self.rental_pending = Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.items[0],
            
            pending_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            confirm_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            complete_date=None,
            cancelled_date=None,

            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="pending",
        )
        
        self.rental_confirmed = Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.items[0],
            
            pending_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            confirm_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            complete_date=None,
            cancelled_date=None,

            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="confirmed",
        )
        
        self.rental_completed = Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.items[0],
            
            pending_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            confirm_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            complete_date=None,
            cancelled_date=None,

            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="completed",
        )

        self.rental_cancelled = Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.items[0],
            
            pending_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            confirm_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
            complete_date=None,
            cancelled_date=None,

            start_date=datetime.now().date() + timedelta(1),
            end_date=datetime.now().date() + timedelta(2),
            status="cancelled",
        )

        self.review = [Review.objects.create(
            author=self.renter,
            rental=self.rental_completed,
            rating=5,
            comment="Test comment",
            created_date=datetime(2024, 2, 7, tzinfo=timezone.utc),
        )]

    def test_item_state_unauthenticated(self):
        context = {'item': self.items[0], 'user': None}
        context.update({'user_state': ConcreteUserIsNotItemOwner(context)})

        item_state = ItemState(context)

        # check values
        self.assertIsNone(item_state.view_active_rental_details(context))
        self.assertQuerysetEqual(item_state.view_item_reviews(context), self.review)
        self.assertQuerysetEqual(item_state.view_item_reviews_by_user(context), [])

        # check boolean
        self.assertTrue(item_state.show_item_messages(context))
        self.assertFalse(item_state.can_cancel_rental(context))
        self.assertFalse(item_state.can_accept_rental(context))
        self.assertFalse(item_state.can_complete_rental(context))
        self.assertFalse(item_state.can_add_rental(context))
        self.assertFalse(item_state.can_edit_item(context))

    def test_pending_rental_state_owner(self):
        # Login as the user
        self.client.login(username="owner", password="testpassword1")

        context_owner = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsItemOwner(context_owner)

        context_owner.update({'user_state': user_state})

        concrete_item_state = ItemState(context_owner)

        active_rentals_obj = self.rental_pending

        context_owner['active_rental'] = active_rentals_obj
        
        if active_rentals_obj:
            if active_rentals_obj.status=='pending':
                concrete_item_state = ConcreteRentalPending(context_owner)

            #can complete?
            elif active_rentals_obj.status=='confirmed':
                concrete_item_state = ConcreteRentalOngoing(context_owner)

        self.assertFalse(concrete_item_state.show_item_messages(context_owner))
        self.assertTrue(concrete_item_state.can_cancel_rental(context_owner))
        self.assertFalse(concrete_item_state.can_accept_rental(context_owner))
        self.assertFalse(concrete_item_state.can_complete_rental(context_owner))
        self.assertFalse(concrete_item_state.can_add_rental(context_owner))
        self.assertFalse(concrete_item_state.can_edit_item(context_owner))

    def test_comfirmed_rental_state_owner(self):
        # Login as the user
        self.client.login(username="owner", password="testpassword1")

        context_owner = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsItemOwner(context_owner)

        context_owner.update({'user_state': user_state})

        concrete_item_state = ItemState(context_owner)

        active_rentals_obj = self.rental_confirmed

        context_owner['active_rental'] = active_rentals_obj
        
        if active_rentals_obj:
            if active_rentals_obj.status=='pending':
                concrete_item_state = ConcreteRentalPending(context_owner)

            #can complete?
            elif active_rentals_obj.status=='confirmed':
                concrete_item_state = ConcreteRentalOngoing(context_owner)

        self.assertFalse(concrete_item_state.show_item_messages(context_owner))
        self.assertFalse(concrete_item_state.can_cancel_rental(context_owner))
        self.assertFalse(concrete_item_state.can_accept_rental(context_owner))
        self.assertTrue(concrete_item_state.can_complete_rental(context_owner))
        self.assertFalse(concrete_item_state.can_add_rental(context_owner))
        self.assertFalse(concrete_item_state.can_edit_item(context_owner))        

    def test_empty_rental_state_owner(self):
        # Login as the user
        self.client.login(username="owner", password="testpassword1")

        context_owner = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsItemOwner(context_owner)

        context_owner.update({'user_state': user_state})

        concrete_item_state = ItemState(context_owner)

        context_owner['active_rental'] = None

        self.assertFalse(concrete_item_state.show_item_messages(context_owner))
        self.assertFalse(concrete_item_state.can_cancel_rental(context_owner))
        self.assertFalse(concrete_item_state.can_accept_rental(context_owner))
        self.assertFalse(concrete_item_state.can_complete_rental(context_owner))
        self.assertTrue(concrete_item_state.can_add_rental(context_owner))
        self.assertTrue(concrete_item_state.can_edit_item(context_owner))        

    def test_pending_rental_state_renter(self):
        # Login as the user
        self.client.login(username="renter", password="testpassword1")

        context_renter = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsNotItemOwner(context_renter)

        context_renter.update({'user_state': user_state})

        concrete_item_state = ItemState(context_renter)

        active_rentals_obj = self.rental_pending

        context_renter['active_rental'] = active_rentals_obj
        
        if active_rentals_obj:
            if active_rentals_obj.status=='pending':
                concrete_item_state = ConcreteRentalPending(context_renter)

            #can complete?
            elif active_rentals_obj.status=='confirmed':
                concrete_item_state = ConcreteRentalOngoing(context_renter)

        self.assertTrue(concrete_item_state.show_item_messages(context_renter))
        self.assertFalse(concrete_item_state.can_cancel_rental(context_renter))
        self.assertTrue(concrete_item_state.can_accept_rental(context_renter))
        self.assertFalse(concrete_item_state.can_complete_rental(context_renter))
        self.assertFalse(concrete_item_state.can_add_rental(context_renter))
        self.assertFalse(concrete_item_state.can_edit_item(context_renter))

    def test_comfirmed_rental_state_renter(self):
        # Login as the user
        self.client.login(username="renter", password="testpassword1")

        context_renter = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsNotItemOwner(context_renter)

        context_renter.update({'user_state': user_state})

        concrete_item_state = ItemState(context_renter)

        active_rentals_obj = self.rental_confirmed

        context_renter['active_rental'] = active_rentals_obj
        
        if active_rentals_obj:
            if active_rentals_obj.status=='pending':
                concrete_item_state = ConcreteRentalPending(context_renter)

            #can complete?
            elif active_rentals_obj.status=='confirmed':
                concrete_item_state = ConcreteRentalOngoing(context_renter)

        self.assertTrue(concrete_item_state.show_item_messages(context_renter))
        self.assertFalse(concrete_item_state.can_cancel_rental(context_renter))
        self.assertFalse(concrete_item_state.can_accept_rental(context_renter))
        self.assertFalse(concrete_item_state.can_complete_rental(context_renter))
        self.assertFalse(concrete_item_state.can_add_rental(context_renter))
        self.assertFalse(concrete_item_state.can_edit_item(context_renter))

    def test_empty_rental_state_renter(self):
        # Login as the user
        self.client.login(username="renter", password="testpassword1")

        context_renter = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsNotItemOwner(context_renter)

        context_renter.update({'user_state': user_state})

        concrete_item_state = ItemState(context_renter)

        context_renter['active_rental'] = None

        self.assertTrue(concrete_item_state.show_item_messages(context_renter))
        self.assertFalse(concrete_item_state.can_cancel_rental(context_renter))
        self.assertFalse(concrete_item_state.can_accept_rental(context_renter))
        self.assertFalse(concrete_item_state.can_complete_rental(context_renter))
        self.assertFalse(concrete_item_state.can_add_rental(context_renter))
        self.assertFalse(concrete_item_state.can_edit_item(context_renter))