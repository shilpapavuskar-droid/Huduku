
from django.contrib import admin
from django.urls import path, include
from brain import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Brain proxy API (to auth_service, listing_service, location, etc.)
    path("api/v1/brain/categories", views.get_categories),
    path("api/v1/brain/listings", views.get_all_listings),
    path("api/v1/brain/user/<int:user_id>/listings", views.get_user_listings),
    path("api/v1/brain/listings-with-images", views.get_listings_with_images),
    path(
        "api/v1/brain/listing/<int:listing_id>/image/upload",
        views.upload_listing_image,
    ),
    path(
        "api/v1/brain/listing/<int:listing_id>/with-images",
        views.get_listing_details,
    ),

    # Auth-related proxy endpoints
    path("api/v1/brain/register", views.register),
    path("api/v1/brain/login", views.login),
    path("api/v1/brain/users/change_password", views.change_password),
    path("api/v1/brain/update_user_profile", views.update_user_profile),
    path("api/v1/brain/users/<int:user_id>", views.get_user),

    # Listing CRUD proxy
    path("api/v1/brain/listing/create", views.create_listing),
    path("api/v1/brain/listing/<int:listing_id>", views.update_listing),
    path("api/v1/brain/listing/<int:listing_id>/delete", views.delete_listing),

    # Location proxy
    path("api/v1/brain/states", views.get_states),
    path("api/v1/brain/states/<str:state_slug>/districts", views.get_districts),
    path(
        "api/v1/brain/states/<str:state_slug>/districts/<str:district_slug>/cities",
        views.get_cities,
    ),
    path(
        "api/v1/brain/states/<str:state_slug>/districts/"
        "<str:district_slug>/cities/<str:city_slug>/localities",
        views.get_localities,
    ),

    # UI (HTMX + templates)
    path("", include(("huduku_ui.urls", "huduku_ui"), namespace="huduku_ui")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)