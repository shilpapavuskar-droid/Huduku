
from django.shortcuts import render
from django.conf import settings
from django.core.cache import cache
import hashlib
import json

import httpx

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .auth_client import verify_user


AUTH_URL = "http://auth-srv:8000/api/v1"
LISTING_URL = "http://listing-srv:8000/api/v1"
REGION_URL = "http://region-srv:5000"


def _forward_auth_header(request) -> dict:
    auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
    return {"Authorization": auth_header} if auth_header else {}


@api_view(["GET"])
def get_categories(request):
    with httpx.Client() as client:
        resp = client.get(f"{LISTING_URL}/category")
        if resp.status_code != 200:
            return Response(
                {"detail": resp.text},
                status=resp.status_code,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_all_listings(request):
    params = dict(request.GET.items())
    with httpx.Client() as client:
        resp = client.get(f"{LISTING_URL}/listings", params=params)
        if resp.status_code != 200:
            return Response(
                {"detail": resp.text},
                status=resp.status_code,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_user_listings(request, user_id: int):
    with httpx.Client() as client:
        user_resp = client.get(f"{AUTH_URL}/users/{user_id}")
        if user_resp.status_code != 200:
            return Response(
                {"detail": user_resp.text},
                status=user_resp.status_code,
            )
        user = user_resp.json()

        listings_resp = client.get(
            f"{LISTING_URL}/listings",
            params={"user_id": user_id},
        )
        if listings_resp.status_code != 200:
            return Response(
                {"detail": listings_resp.text},
                status=listings_resp.status_code,
            )
        listings = listings_resp.json()

    return Response(
        {"user": user, "listings": listings},
        status=status.HTTP_200_OK,
    )



@api_view(["GET"])
def get_listings_with_images(request):
    """
        Proxy: list listings and attach their images.
        UI calls:
          GET `/api/v1/brain/listings-with-images?...`
        listing_service calls:
          - GET `/listings` with filters
          - GET `/listing/{id}/images/` per listing
    """
    # build a cache key from query params
    raw_key = json.dumps(sorted(request.GET.items()))
    cache_key = "listings_with_images:" + hashlib.sha256(raw_key.encode()).hexdigest()

    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached, status=status.HTTP_200_OK)
    params = {}
    for key in [
        "location",
        "category",
        "min_price",
        "max_price",
        "user_id",
        "state_slug",
        "district_slug",
        "city_slug",
        "locality_slug",
        "category_slug",
        "slug",  # optional, if you later support slug filtering in listing_service
    ]:
        value = request.GET.get(key)
        if value:
            params[key] = value

    with httpx.Client() as client:
        core_resp = client.get(f"{LISTING_URL}/listings", params=params, timeout=5.0)
        if core_resp.status_code != 200:
            return Response(
                {"detail": core_resp.text},
                status=core_resp.status_code,
            )

        listings = core_resp.json()
        if not isinstance(listings, list):
            listings = [listings]

        results = []
        for item in listings:
            listing_id = item.get("id")
            images = []

            if listing_id:
                img_resp = client.get(
                    f"{LISTING_URL}/listing/{listing_id}/images/",
                    timeout=5.0,
                )
                if img_resp.status_code == 200:
                    # listing_service already returns `image` as a URL, keep as is
                    images = img_resp.json()

            item["images"] = images
            results.append(item)
    cache.set(cache_key, results, timeout=60)
    return Response(results, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_listing_details(request, listing_id: int):
    """
    Detail page: return a single listing with its images.
    """
    with httpx.Client() as client:
        # listing core data
        core_resp = client.get(f"{LISTING_URL}/listing/{listing_id}", timeout=5.0)
        if core_resp.status_code != 200:
            return Response(
                {"detail": core_resp.text},
                status=core_resp.status_code,
            )
        listing = core_resp.json()

        # listing images
        img_resp = client.get(
            f"{LISTING_URL}/listing/{listing_id}/images/",
            timeout=5.0,
        )
        images = img_resp.json() if img_resp.status_code == 200 else []

    listing["images"] = images
    return Response(listing, status=status.HTTP_200_OK)

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload_listing_image(request, listing_id: int):
    files = {}
    image_file = request.FILES.get("image")
    if not image_file:
        # support `<input name="images">` from UI: take first one
        images = request.FILES.getlist("images")
        if images:
            image_file = images[0]

    if not image_file:
        return Response({"detail": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

    files["image"] = (image_file.name, image_file.read(), image_file.content_type)

    with httpx.Client() as client:
        resp = client.post(
            f"{LISTING_URL}/listing/{listing_id}/image/upload",
            files=files,
            headers=_forward_auth_header(request),
            timeout=15.0,
        )
        if resp.status_code not in (200, 201):
            return Response({"detail": resp.text}, status=resp.status_code)
        return Response(resp.json(), status=resp.status_code)


@api_view(["POST"])
@parser_classes([JSONParser])
def register(request):
    """
    Proxy register:
    UI -> Brain /register -> auth-srv /api/v1/register

    auth-srv now returns 201 + user JSON on success,
    and 400 + {"detail": "..."} (e.g. "Email already registered")
    on validation errors.
    """
    data = request.data

    with httpx.Client() as client:
        resp = client.post(f"{AUTH_URL}/register", json=data, timeout=5.0)

    # Try to decode JSON body if present
    try:
        payload = resp.json()
    except ValueError:
        payload = None

    # Non-201: just normalize to a JSON error payload
    if resp.status_code != status.HTTP_201_CREATED:
        if not isinstance(payload, dict) or not payload:
            payload = {"detail": resp.text or "Registration failed."}
        return Response(payload, status=resp.status_code)

    # Success: forward auth-srv response (created user)
    if not isinstance(payload, dict) or not payload:
        payload = {"detail": "Registered successfully"}
    return Response(payload, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@parser_classes([JSONParser])
def login(request):
    data = request.data
    with httpx.Client() as client:
        resp = client.post(f"{AUTH_URL}/login", json=data)
        if resp.status_code != 200:
            return Response(
                {"detail": resp.text},
                status=resp.status_code,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([JSONParser])
def change_password(request):
    data = request.data
    with httpx.Client() as client:
        resp = client.post(f"{AUTH_URL}/users/change_password", json=data)
        if resp.status_code != 200:
            return Response(
                {"detail": resp.text},
                status=resp.status_code,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_user(request, user_id: int):
    with httpx.Client() as client:
        try:
            resp = client.get(
                f"{AUTH_URL}/users/{user_id}",
                timeout=5.0,
            )
        except httpx.RequestError:
            return Response(
                {"detail": "Auth service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    if resp.status_code != 200:
        return Response(
            {"detail": "Failed to fetch user"},
            status=resp.status_code,
        )

    return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([JSONParser])
def update_user_profile(request):
    user = verify_user(request)
    if not user:
        return Response(
            {"detail": "Please log in to continue"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = user.get("user_id")

    with httpx.Client() as client:
        resp = client.post(
            f"{AUTH_URL}/update_user_profile/{user_id}",
            json=request.data,
        )
        if resp.status_code != 200:
            return Response(
                {"detail": resp.text},
                status=resp.status_code,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([JSONParser])
def create_listing(request):
    """
    Brain endpoint used by UI `sell_submit`.

    Expects JSON:
    title, category (int), price (float/int),
    state_slug, district_slug, city_slug, locality_slug,
    optional is_active.

    Adds `user_id` and builds `location` path, then forwards to listing service.
    """
    user = verify_user(request)
    if not user:
        return Response(
            {"detail": "Please log in to continue"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = user.get("user_id")

    data = request.data

    # validate presence of location parts
    required_location_parts = [
        "state_slug",
        "district_slug",
        "city_slug",
        "locality_slug",
    ]
    for part in required_location_parts:
        if part not in data or not str(data[part]).strip():
            return Response(
                {"detail": f"Missing location part: {part}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # build hierarchical location path
    location_path = (
        f"{data['state_slug']}/"
        f"{data['district_slug']}/"
        f"{data['city_slug']}/"
        f"{data['locality_slug']}"
    )

    payload = {
        "user_id": user_id,
        "title": data.get("title"),
        "category": data.get("category"),
        "price": data.get("price"),
        "locality_slug": data.get("locality_slug"),
        "location": location_path,
        "is_active": data.get("is_active", True),
    }

    with httpx.Client() as client:
        resp = client.post(f"{LISTING_URL}/listing/create", json=payload)
        if resp.status_code not in (200, 201):
            return Response(
                {"detail": resp.text},
                status=resp.status_code,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["PUT"])
@parser_classes([JSONParser])
def update_listing(request, listing_id: int):
    user = verify_user(request)
    if not user:
        return Response(
            {"detail": "Please log in to continue"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = user.get("user_id")
    is_staff = user.get("is_staff", False)

    with httpx.Client() as client:
        # fetch listing to check ownership
        resp = client.get(f"{LISTING_URL}/listing/{listing_id}")
        if resp.status_code != 200:
            return Response(
                {"detail": "Listing not found"},
                status=resp.status_code,
            )
        listing = resp.json()

        if listing.get("owner_user_id") != user_id and not is_staff:
            return Response(
                {"detail": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        update_resp = client.put(
            f"{LISTING_URL}/listing/{listing_id}",
            json=request.data,
        )
        if update_resp.status_code != 200:
            return Response(
                {"detail": update_resp.text},
                status=update_resp.status_code,
            )
        return Response(update_resp.json(), status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_listing(request, listing_id: int):
    user = verify_user(request)
    if not user:
        return Response(
            {"detail": "Please log in to continue"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    user_id = user.get("user_id")
    is_staff = user.get("is_staff", False)

    with httpx.Client() as client:
        resp = client.get(f"{LISTING_URL}/listing/{listing_id}")
        if resp.status_code != 200:
            return Response(
                {"detail": "Listing not found"},
                status=resp.status_code,
            )

        listing = resp.json()
        if listing.get("owner_user_id") != user_id and not is_staff:
            return Response(
                {"detail": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        delete_resp = client.delete(f"{LISTING_URL}/listing/{listing_id}")
        if delete_resp.status_code != 200:
            return Response(
                {"detail": delete_resp.text},
                status=delete_resp.status_code,
            )
        return Response(delete_resp.json(), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_states(request):
    with httpx.Client() as client:
        resp = client.get(f"{REGION_URL}/states")
        if resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch states"},
                status=resp.status_code,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_districts(request, state_slug: str):
    with httpx.Client() as client:
        state_resp = client.get(
            f"{REGION_URL}/states",
            params={"slug": state_slug},
        )
        if state_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch state"},
                status=state_resp.status_code,
            )
        states = state_resp.json()
        if not states:
            return Response(
                {"detail": "State not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        state_code = states[0]["code"]
        dist_resp = client.get(
            f"{REGION_URL}/states/{state_code}/districts"
        )
        if dist_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch districts"},
                status=dist_resp.status_code,
            )
        return Response(dist_resp.json(), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_cities(request, state_slug: str, district_slug: str):
    with httpx.Client() as client:
        state_resp = client.get(
            f"{REGION_URL}/states",
            params={"slug": state_slug},
        )
        if state_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch state"},
                status=state_resp.status_code,
            )
        states = state_resp.json()
        if not states:
            return Response(
                {"detail": "State not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        state_code = states[0]["code"]

        dist_resp = client.get(
            f"{REGION_URL}/states/{state_code}/districts"
        )
        if dist_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch districts"},
                status=dist_resp.status_code,
            )
        districts = dist_resp.json()
        district = next(
            (d for d in districts if d["slug"] == district_slug),
            None,
        )
        if not district:
            return Response(
                {"detail": "District not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        city_resp = client.get(
            f"{REGION_URL}/states/{state_code}/districts/{district['code']}/cities"
        )
        if city_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch cities"},
                status=city_resp.status_code,
            )
        return Response(city_resp.json(), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_localities(request, state_slug: str, district_slug: str, city_slug: str):
    with httpx.Client() as client:
        state_resp = client.get(
            f"{REGION_URL}/states",
            params={"slug": state_slug},
        )
        if state_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch state"},
                status=state_resp.status_code,
            )
        states = state_resp.json()
        if not states:
            return Response(
                {"detail": "State not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        state_code = states[0]["code"]

        dist_resp = client.get(
            f"{REGION_URL}/states/{state_code}/districts"
        )
        if dist_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch districts"},
                status=dist_resp.status_code,
            )
        districts = dist_resp.json()
        district = next(
            (d for d in districts if d["slug"] == district_slug),
            None,
        )
        if not district:
            return Response(
                {"detail": "District not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        city_resp = client.get(
            f"{REGION_URL}/states/{state_code}/districts/{district['code']}/cities"
        )
        if city_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch cities"},
                status=city_resp.status_code,
            )
        cities = city_resp.json()
        city = next(
            (c for c in cities if c["slug"] == city_slug),
            None,
        )
        if not city:
            return Response(
                {"detail": "City not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        loc_resp = client.get(
            f"{REGION_URL}/states/{state_code}/districts/"
            f"{district['code']}/cities/{city['code']}/locality"
        )
        if loc_resp.status_code != 200:
            return Response(
                {"detail": "Failed to fetch localities"},
                status=loc_resp.status_code,
            )
        return Response(loc_resp.json(), status=status.HTTP_200_OK)