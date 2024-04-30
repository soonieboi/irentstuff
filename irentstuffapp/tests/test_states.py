from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.core import mail
from django.urls import reverse
from irentstuffapp.models import Item, Category, Rental, Purchase, Review, Message, ItemStatesCaretaker, RentalEmailSender, RentalMessageSender
from irentstuffapp.states import (ItemState, ConcreteRentalCompleted, ConcreteRentalPending, ConcreteRentalOrPurchaseOngoing,
                                  ConcretePurchaseReserved, ConcretePurchaseCompleted,
                                  ConcreteUserIsItemOwner, ConcreteUserIsNotItemOwner)

import logging
import pytz

logging.basicConfig(level=logging.DEBUG)
sgt = pytz.timezone('Asia/Singapore')

# owner actions
# owner can cancel rental if rental is not accepted yet (rental status: pending)
# owner can complete rental if rental is accepted (rental status: confirmed)
# owner can add rental if there are no active rental
# owner can edit/ delete item if there are no active rental

# renter actions
# renter can accept rental if rental date has not started (rental status: pending)


class ItemStateRentalTestCase(TestCase):
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
                created_date=datetime(2024, 2, 7, tzinfo=sgt),
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
                created_date=datetime(2024, 2, 7, tzinfo=sgt),
                deleted_date=None,
            )
        ]

        self.rental_pending = Rental.objects.create(
            owner=self.owner,
            renter=self.renter,
            item=self.items[0],

            pending_date=datetime(2024, 2, 7, tzinfo=sgt),
            confirm_date=datetime(2024, 2, 7, tzinfo=sgt),
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

            pending_date=datetime(2024, 2, 7, tzinfo=sgt),
            confirm_date=datetime(2024, 2, 7, tzinfo=sgt),
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

            pending_date=datetime(2024, 2, 7, tzinfo=sgt),
            confirm_date=datetime(2024, 2, 7, tzinfo=sgt),
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

            pending_date=datetime(2024, 2, 7, tzinfo=sgt),
            confirm_date=datetime(2024, 2, 7, tzinfo=sgt),
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
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
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
            if active_rentals_obj.status == 'pending':
                concrete_item_state = ConcreteRentalPending(context_owner)

            # can complete?
            elif active_rentals_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_owner)

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
            if active_rentals_obj.status == 'pending':
                concrete_item_state = ConcreteRentalPending(context_owner)

            # can complete?
            elif active_rentals_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_owner)

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
        context_owner['pending_purchase'] = None

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
            if active_rentals_obj.status == 'pending':
                concrete_item_state = ConcreteRentalPending(context_renter)

            # can complete?
            elif active_rentals_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_renter)

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
            if active_rentals_obj.status == 'pending':
                concrete_item_state = ConcreteRentalPending(context_renter)

            # can complete?
            elif active_rentals_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_renter)

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


class ItemStatePurchaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(
            username="owner", password="testpassword1", email="owner@test.com"
        )
        self.buyer = User.objects.create_user(
            username="buyer", password="testpassword3", email="buyer@test.com"
        )

        self.category = Category.objects.create(name="testcategory")

        self.items = [
            Item.objects.create(
                owner=self.owner,
                title="State Test Purchase Item",
                description="Test purchase description",
                category=self.category,
                condition="excellent",
                price_per_day=10.00,
                deposit=50.00,
                image="item_images/test_image.jpg",
                created_date=datetime(2024, 2, 7, tzinfo=sgt),
                deleted_date=None,
            ),
        ]

        self.purchase_reserved = Purchase.objects.create(
            owner=self.owner,
            buyer=self.buyer,
            item=self.items[0],

            deal_reserved_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_confirmed_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_complete_date=None,
            deal_cancelled_date=None,

            deal_date=datetime.now().date() + timedelta(1),
            status="reserved",
        )

        self.purchase_confirmed = Purchase.objects.create(
            owner=self.owner,
            buyer=self.buyer,
            item=self.items[0],

            deal_reserved_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_confirmed_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_complete_date=None,
            deal_cancelled_date=None,

            deal_date=datetime.now().date() + timedelta(1),
            status="confirmed",
        )

        self.purchase_completed = Purchase.objects.create(
            owner=self.owner,
            buyer=self.buyer,
            item=self.items[0],

            deal_reserved_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_confirmed_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_complete_date=None,
            deal_cancelled_date=None,

            deal_date=datetime.now().date() + timedelta(1),
            status="completed",
        )

        self.purchase_cancelled = Purchase.objects.create(
            owner=self.owner,
            buyer=self.buyer,
            item=self.items[0],

            deal_reserved_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_confirmed_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_complete_date=None,
            deal_cancelled_date=None,

            deal_date=datetime.now().date() + timedelta(1),
            status="cancelled",
        )

        self.purchase_invalid = Purchase.objects.create(
            owner=self.owner,
            buyer=self.buyer,
            item=self.items[0],

            deal_reserved_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_confirmed_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_complete_date=None,
            deal_cancelled_date=None,

            deal_date=datetime.now().date() - timedelta(5),
            status="reserved",
        )

    def test_reserved_purchase_state_owner(self):
        self.client.login(username="owner", password="testpassword1")

        context_owner = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsItemOwner(context_owner)

        context_owner.update({'user_state': user_state})

        concrete_item_state = ItemState(context_owner)

        pending_purchase_obj = self.purchase_reserved

        context_owner['pending_purchase'] = pending_purchase_obj
        context_owner['active_rental'] = None

        if pending_purchase_obj:
            if pending_purchase_obj.status == 'reserved':
                concrete_item_state = ConcretePurchaseReserved(context_owner)

            elif pending_purchase_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_owner)

        self.assertFalse(concrete_item_state.show_item_messages(context_owner))
        self.assertTrue(concrete_item_state.can_cancel_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_accept_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_complete_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_add_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_edit_item(context_owner))

    def test_confirmed_purchase_state_owner(self):
        self.client.login(username="owner", password="testpassword1")

        context_owner = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsItemOwner(context_owner)

        context_owner.update({'user_state': user_state})

        concrete_item_state = ItemState(context_owner)

        pending_purchase_obj = self.purchase_confirmed

        context_owner['pending_purchase'] = pending_purchase_obj
        context_owner['active_rental'] = None

        if pending_purchase_obj:
            if pending_purchase_obj.status == 'reserved':
                concrete_item_state = ConcretePurchaseReserved(context_owner)

            elif pending_purchase_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_owner)

        self.assertFalse(concrete_item_state.show_item_messages(context_owner))
        self.assertFalse(concrete_item_state.can_cancel_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_accept_purchase(context_owner))
        self.assertTrue(concrete_item_state.can_complete_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_add_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_edit_item(context_owner))

    def test_empty_purchase_state_owner(self):
        self.client.login(username="owner", password="testpassword1")

        context_owner = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsItemOwner(context_owner)

        context_owner.update({'user_state': user_state})

        concrete_item_state = ItemState(context_owner)

        context_owner['active_rental'] = None
        context_owner['pending_purchase'] = None

        self.assertFalse(concrete_item_state.show_item_messages(context_owner))
        self.assertFalse(concrete_item_state.can_cancel_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_accept_purchase(context_owner))
        self.assertFalse(concrete_item_state.can_complete_purchase(context_owner))
        self.assertTrue(concrete_item_state.can_add_purchase(context_owner))
        self.assertTrue(concrete_item_state.can_edit_item(context_owner))

    def test_reserved_purchase_state_buyer(self):
        self.client.login(username="buyer", password="testpassword3")

        context_buyer = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsNotItemOwner(context_buyer)

        context_buyer.update({'user_state': user_state})

        concrete_item_state = ItemState(context_buyer)

        pending_purchase_obj = self.purchase_reserved

        context_buyer['pending_purchase'] = pending_purchase_obj

        if pending_purchase_obj:
            if pending_purchase_obj.status == 'reserved':
                concrete_item_state = ConcretePurchaseReserved(context_buyer)

            elif pending_purchase_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_buyer)

        self.assertTrue(concrete_item_state.show_item_messages(context_buyer))
        self.assertFalse(concrete_item_state.can_cancel_purchase(context_buyer))
        self.assertTrue(concrete_item_state.can_accept_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_complete_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_add_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_edit_item(context_buyer))

    def test_confirmed_purchase_state_buyer(self):
        self.client.login(username="buyer", password="testpassword3")

        context_buyer = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsNotItemOwner(context_buyer)

        context_buyer.update({'user_state': user_state})

        concrete_item_state = ItemState(context_buyer)

        pending_purchase_obj = self.purchase_confirmed

        context_buyer['pending_purchase'] = pending_purchase_obj

        if pending_purchase_obj:
            if pending_purchase_obj.status == 'reserved':
                concrete_item_state = ConcretePurchaseReserved(context_buyer)

            elif pending_purchase_obj.status == 'confirmed':
                concrete_item_state = ConcreteRentalOrPurchaseOngoing(context_buyer)

        self.assertTrue(concrete_item_state.show_item_messages(context_buyer))
        self.assertFalse(concrete_item_state.can_cancel_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_accept_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_complete_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_add_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_edit_item(context_buyer))

    def test_empty_purchase_state_buyer(self):
        self.client.login(username="buyer", password="testpassword3")

        context_buyer = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsNotItemOwner(context_buyer)

        context_buyer.update({'user_state': user_state})

        concrete_item_state = ItemState(context_buyer)

        context_buyer['pending_purchase'] = None

        self.assertTrue(concrete_item_state.show_item_messages(context_buyer))
        self.assertFalse(concrete_item_state.can_cancel_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_accept_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_complete_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_add_purchase(context_buyer))
        self.assertFalse(concrete_item_state.can_edit_item(context_buyer))

    def test_can_accept_purchase_no_deal_date(self):
        self.client.login(username="buyer", password="testpassword3")

        context_buyer = {'item': self.items[0], 'user': self.client}

        user_state = ConcreteUserIsNotItemOwner(context_buyer)

        context_buyer.update({'user_state': user_state})

        concrete_item_state = ItemState(context_buyer)

        pending_purchase_obj = self.purchase_invalid

        context_buyer['pending_purchase'] = pending_purchase_obj

        # Check if can_accept_purchase returns False
        self.assertFalse(concrete_item_state.can_accept_purchase(context_buyer))


class ConcretePurchaseCompletedTestCase(TestCase):
    def setUp(self):
        # Create necessary objects for testing
        self.owner = User.objects.create_user(
            username="owner", password="testpassword1", email="owner@test.com"
        )
        self.buyer = User.objects.create_user(
            username="buyer", password="testpassword3", email="buyer@test.com"
        )
        self.category = Category.objects.create(name="testcategory")

        self.item = Item.objects.create(
            owner=self.owner,
            title="State Test Purchase Item",
            description="Test purchase description",
            category=self.category,
            condition="excellent",
            price_per_day=10.00,
            deposit=50.00,
            image="item_images/test_image.jpg",
            created_date=datetime(2024, 2, 7, tzinfo=sgt),
            deleted_date=None,
        )

        self.purchase = Purchase.objects.create(
            owner=self.owner,
            buyer=self.buyer,
            item=self.item,
            deal_reserved_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_confirmed_date=datetime(2024, 2, 7, tzinfo=sgt),
            deal_complete_date=datetime.now(tz=sgt),  # Completed purchase
            deal_cancelled_date=None,
            deal_date=datetime.now(tz=sgt) + timedelta(1),
            status="completed",
        )

    def test_can_accept_purchase_as_owner(self):
        self.client.login(username="owner", password="testpassword1")
        context_owner = {'item': self.item, 'user': self.client}
        user_state = ConcreteUserIsItemOwner(context_owner)
        context_owner.update({'user_state': user_state})
        concrete_item_state = ItemState(context_owner)
        pending_purchase_obj = self.purchase
        context_owner['pending_purchase'] = pending_purchase_obj

        # Check if can_accept_purchase returns True for the owner
        self.assertFalse(concrete_item_state.can_accept_purchase(context_owner))

    def test_can_accept_purchase_as_buyer(self):
        self.client.login(username="buyer", password="testpassword3")
        context_buyer = {'item': self.item, 'user': self.client}
        user_state = ConcreteUserIsNotItemOwner(context_buyer)
        context_buyer.update({'user_state': user_state})
        concrete_item_state = ItemState(context_buyer)
        pending_purchase_obj = self.purchase
        context_buyer['pending_purchase'] = pending_purchase_obj

        # Check if can_accept_purchase returns False for the buyer
        self.assertFalse(concrete_item_state.can_accept_purchase(context_buyer))

    def test_can_accept_purchase_unauthenticated(self):
        context = {'item': self.item, 'user_state': None}
        concrete_item_state = ItemState(context)
        pending_purchase_obj = self.purchase
        context['pending_purchase'] = pending_purchase_obj

        # Check if can_accept_purchase returns False for unauthenticated user
        self.assertFalse(concrete_item_state.can_accept_purchase(context))
