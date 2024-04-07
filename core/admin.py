# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'name', 'phone_number', 'role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'role')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_verified','is_superuser', 'groups', 'user_permissions')}),
        # ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom fields', {'fields': ('token', 'role')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active', 'role')}
        ),
    )
    search_fields = ('email', 'name')
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)


admin.site.register(HomeBlocks)
admin.site.register(HomeSlides)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['categoryName']

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['collectionName']

@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ['gender']

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['sizes']

@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['productName', 'price', 'isInOffer', 'offerPrice', 'gender', 'category', 'collection']

@admin.register(reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'content', 'created_at']


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['uniqueId', 'user', 'total_amount', 'status', 'created_at', 'updated_at']


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'anonymous_id')  # Use a custom method to display the user's name
    search_fields = ('user__name', 'anonymous_id')  # Update the search field accordingly
    inlines = [WishlistItemInline]

    def get_user_name(self, obj):
        return obj.user.name if obj.user else "Anonymous"  # Return user's name or "Anonymous" if user is not specified
    get_user_name.short_description = 'User'  # Set a custom name for the column

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('wishlist', 'product')
    search_fields = ('wishlist__user__name', 'product__name')


admin.site.register(Cart)
admin.site.register(CartItems)
admin.site.register(Order)
admin.site.register(OrderItems)