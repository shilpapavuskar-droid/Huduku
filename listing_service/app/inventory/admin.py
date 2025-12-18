from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Listing,  Review, Favorite, ListingImage


# -------------------------
# CATEGORY ADMIN
# -------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent','slug')
    search_fields = ('name', 'slug')
    list_filter = ('parent','slug')
    ordering = ('name',)


# -------------------------
# LISTING ADMIN
# -------------------------
@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'owner_user_id', 'category', 'price',
        'location', 'is_active', 'created_at','updated_at'
    )
    search_fields = ('title', 'description', 'location')
    list_filter = ('is_active', 'category')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


# -------------------------
# LISTING Image ADMIN
# -------------------------
@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'image_preview', 'created_at', 'updated_at')
    list_filter = ('created_at', )
    search_fields = ('listing__title',)
    ordering = ('created_at',)
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" />',
                obj.image.url
            )
        return "No Image"

    image_preview.short_description = "Preview"




# -------------------------
# FAVORITE ADMIN
# -------------------------
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'listing')
    search_fields = ('user_id', 'listing__title')
    list_filter = ('listing',)


# -------------------------
# REGISTER MODELS
# -------------------------

# -------------------------
# REVIEW ADMIN
# -------------------------
# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'listing', 'reviewer_user_id',
#         'rating', 'comment', 'created_at'
#     )
#     search_fields = ('comment', 'listing__title')
#     list_filter = ('rating',)
#     readonly_fields = ('created_at',)
#     ordering = ('-created_at',)
# # Register your models here.
