import uuid
from django.db import models
from rest_framework import serializers
from django.contrib.auth.models import User



# ---------------------------
# CATEGORY MODEL
# ---------------------------
class Category(models.Model):
    id = models.AutoField(primary_key=True,editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------
# LISTING MODEL
# ---------------------------
class Listing(models.Model):
    id = models.AutoField(primary_key=True,editable=False)

    owner_user_id = models.IntegerField()  # if you don’t have a User model
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='listings'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ---------------------------
# LISTING MEDIA MODEL
# ---------------------------
class ListingImage(models.Model):
    id = models.AutoField(primary_key=True,editable=False)

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to="listings/")  # if media is handled externally (S3, etc.)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Image for {self.listing.title}"

#
# ---------------------------
# REVIEWS MODEL
# ---------------------------
class Review(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.rating}★"

# ---------------------------
# FAVORITES MODEL
# ---------------------------
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')  # prevent duplicate favorites

    def __str__(self):
        return f"Favorite by {self.user.id} for listing {self.listing.id}"

