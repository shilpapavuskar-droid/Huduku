from django.urls import path
from . import views

app_name = "huduku_ui"

urlpatterns = [
    # Home page with optional filters in URL
    path("", views.home, name="home"),
    path(
        "loc/<str:state_slug>/<str:district_slug>/<str:city_slug>/<str:locality_slug>/",
        views.home,
        name="home_by_location",
    ),
    path(
        "cat/<path:category_slug_path>/",
        views.home,
        name="home_by_category",
    ),
    path(
        "loc/<str:state_slug>/<str:district_slug>/<str:city_slug>/<str:locality_slug>/"
        "cat/<path:category_slug_path>/",
        views.home,
        name="home_by_location_category",
    ),

    # Listing details
    path(
        "listing/<slug:listing_slug>/",
        views.listing_detail,
        name="listing_detail",
    ),

    # Sell / create listing (UI)
    path("sell/", views.sell_entrypoint, name="sell"),
    path("sell/form/", views.sell_form, name="sell_form"),  # HTMX partial
    path("sell/submit/", views.sell_submit, name="sell_submit"),

    # Auth modals and actions (delegating to Brain/Auth)
    path("auth/modal/login/", views.login_modal, name="login_modal"),
    path("auth/modal/register/", views.register_modal, name="register_modal"),
    path("auth/login", views.login_submit, name="login_submit"),
    path("auth/register/", views.register_submit, name="register_submit"),
    path("auth/logout/", views.logout_view, name="logout"),

    # Location selector (HTMX partials)
    path("location/states/", views.location_states, name="location_states"),
    path(
        "location/<str:state_slug>/districts/",
        views.location_districts,
        name="location_districts",
    ),
    path(
        "location/<str:state_slug>/<str:district_slug>/cities/",
        views.location_cities,
        name="location_cities",
    ),
    path(
        "location/<str:state_slug>/<str:district_slug>/<str:city_slug>/localities/",
        views.location_localities,
        name="location_localities",
    ),

    # Filters & search (HTMX updates listing grid only)
    path("filters/", views.filters_partial, name="filters_partial"),
    path("listings/grid/", views.listing_grid_partial, name="listing_grid_partial"),

    # Listing owner actions (UI only, call Brain)
    path(
        "listing/<slug:listing_slug>/edit/",
        views.listing_edit,
        name="listing_edit",
    ),
    path(
        "listing/<slug:listing_slug>/delete/",
        views.listing_delete,
        name="listing_delete",
    ),
    path(
        "listing/<slug:listing_slug>/images/upload/",
        views.listing_image_upload,
        name="listing_image_upload",
    ),
    path(
        "listing/<slug:listing_slug>/images/<int:image_id>/delete/",
        views.listing_image_delete,
        name="listing_image_delete",
    ),
]