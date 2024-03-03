from django.contrib import admin

from .models import Item, Category, Rental, Review

# admin.site.register(Item)
admin.site.register(Category)
# admin.site.register(Rental)
admin.site.register(Review)

class RentalAdmin(admin.ModelAdmin):
  list_display = ("item", "start_date", "end_date")
  
admin.site.register(Rental, RentalAdmin)

class ItemAdmin(admin.ModelAdmin):
  list_display = ("title", "description", "price_per_day")
  
admin.site.register(Item, ItemAdmin)
