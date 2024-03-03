from django.test import SimpleTestCase
from django.urls import reverse, resolve
from irentstuffapp.views import (
    items_list,
    item_detail,
    add_item,
    edit_item,
    delete_item,
    add_rental,
    check_user_exists,
    register,
    login_user,
    logout_user,
)
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)


class TestUrls(SimpleTestCase):

    def test_home_url_resolves(self):
        url = reverse("home")
        self.assertEquals(resolve(url).func, items_list)

    def test_items_list_url_resolves(self):
        url = reverse("items_list")
        self.assertEquals(resolve(url).func, items_list)

    def test_items_list_my_url_resolves(self):
        url = reverse("items_list")
        self.assertEquals(resolve(url).func, items_list)

    def test_item_detail_url_resolves(self):
        url = reverse("item_detail", kwargs={"item_id": "4050"})
        self.assertEquals(resolve(url).func, item_detail)

    def test_add_item_url_resolves(self):
        url = reverse("add_item")
        self.assertEquals(resolve(url).func, add_item)

    def test_edit_item_url_resolves(self):
        url = reverse("edit_item", kwargs={"item_id": "4050"})
        self.assertEquals(resolve(url).func, edit_item)

    def test_delete_item_url_resolves(self):
        url = reverse("delete_item", kwargs={"item_id": "4050"})
        self.assertEquals(resolve(url).func, delete_item)

    def test_add_rental_url_resolves(self):
        url = reverse("add_rental", kwargs={"item_id": "4050"})
        self.assertEquals(resolve(url).func, add_rental)

    def test_check_user_exists_url_resolves(self):
        url = reverse("check_user_exists", kwargs={"username": "4050"})
        self.assertEquals(resolve(url).func, check_user_exists)

    def test_register_url_resolves(self):
        url = reverse("register")
        self.assertEquals(resolve(url).func, register)

    def test_login_url_resolves(self):
        url = reverse("login")
        self.assertEquals(resolve(url).func, login_user)

    def test_logout_url_resolves(self):
        url = reverse("logout")
        self.assertEquals(resolve(url).func, logout_user)

    def test_password_reset_resolves(self):
        url = reverse("reset_password")
        self.assertEquals(resolve(url).func.view_class, PasswordResetView)

    def test_password_reset_done_resolves(self):
        url = reverse("password_reset_done")
        self.assertEquals(resolve(url).func.view_class, PasswordResetDoneView)

    def test_password_reset_confirm_resolves(self):
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": "123456", "token": "123456"}
        )
        self.assertEquals(resolve(url).func.view_class, PasswordResetConfirmView)

    def test_password_reset_complete_resolves(self):
        url = reverse("password_reset_complete")
        self.assertEquals(resolve(url).func.view_class, PasswordResetCompleteView)
