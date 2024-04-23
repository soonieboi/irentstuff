from django.contrib import admin

from .models import Item, Category, Rental, Review, Message, Interest, UserInterests

#admin.site.register(Item)
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner',  'category', 'created_date')
    list_filter = ("category", )
    search_fields = ("description", "title", "owner__username", )


#admin.site.register(Rental)
@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('item', 'owner', 'renter', 'start_date', 'end_date', 'status')
    list_filter = ("status", )
    search_fields = ("item__title",  "owner__username", "start_date", )

admin.site.register(Category)
admin.site.register(Review)

#admin.site.register(Message)
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('content', 'item', 'enquiring_user','timestamp' )
    list_filter = ("item", )
    search_fields = ("content", "enquiring_user__username",)

@admin.register(UserInterests)
class UserInterestsAdmin(admin.ModelAdmin):
    list_display = ('user', 'interest')
    search_fields = ("user__username",)

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('created_date', 'get_categories_display', 'discount', 'item_cd_crit')
    search_fields = ("categories__name",)

    def get_categories_display(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])
    
    get_categories_display.short_description = 'Categories'