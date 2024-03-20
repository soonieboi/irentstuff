from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.items_list, name='home'),
    path('stuff/', views.items_list, name='items_list'),
    path('my_stuff/', views.items_list, name='items_list_my'),
    path('stuff/<int:item_id>/', views.item_detail, name='item_detail'),
    path('add_stuff/', views.add_item, name='add_item'),
    path('stuff/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('stuff/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('stuff/<int:item_id>/accept_rental/', views.accept_rental, name='accept_rental'),
    path('stuff/<int:item_id>/complete_rental/', views.complete_rental, name='complete_rental'),
    path('stuff/<int:item_id>/cancel_rental/', views.cancel_rental, name='cancel_rental'),
    path('stuff/<int:item_id>/add_rental/', views.add_rental, name='add_rental'),
    path('stuff/<int:item_id>/add_rental/<str:username>', views.add_rental, name='add_rental'),
    path('stuff/<int:item_id>/messages/', views.item_messages, name='item_messages_list'),
    path('stuff/<int:item_id>/messages/<int:userid>', views.item_messages, name='item_messages'),
    path('stuff/<int:item_id>/review/', views.add_review, name='add_review'),
    path('check_user_exists/<str:username>/', views.check_user_exists, name='check_user_exists'),
    path('inbox/',views.inbox, name='inbox'),
    path('register/',views.register, name='register'),
    path('login/', views.login_user,name='login'),
    path('logout/',views.logout_user,name='logout'),
    path('reset_password',auth_views.PasswordResetView.as_view(template_name='irentstuffapp/password_reset_form.html'),name="reset_password"),
    path('reset_password_sent',auth_views.PasswordResetDoneView.as_view(template_name='irentstuffapp/password_reset_done.html'),name="password_reset_done"),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='irentstuffapp/password_reset_confirm.html'),name="password_reset_confirm"),
    path('reset_password_complete',auth_views.PasswordResetCompleteView.as_view(template_name='irentstuffapp/password_reset_complete.html'),name="password_reset_complete"),
    path('stuff/', views.items_list, name='items_list'),
    path('stuff/category/<int:category_id>/', views.items_list, name='items_list_by_category'), 
]