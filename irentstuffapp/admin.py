from django.contrib import admin

from .models import Item, Category, Rental, Review

admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Rental)
admin.site.register(Review)
