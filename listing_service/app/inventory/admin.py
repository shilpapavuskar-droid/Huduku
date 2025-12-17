from django.contrib import admin
from .models import Category, Listing, ListingMedia, Review, Favorite


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
# LISTING MEDIA ADMIN
# -------------------------
@admin.register(ListingMedia)
class ListingMediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'media_id', 'type')
    list_filter = ('type',)
    search_fields = ('listing__title',)
    ordering = ('listing',)


# -------------------------
# REVIEW ADMIN
# -------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'listing', 'reviewer_user_id',
        'rating', 'comment', 'created_at'
    )
    search_fields = ('comment', 'listing__title')
    list_filter = ('rating',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


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

# Register your models here.
