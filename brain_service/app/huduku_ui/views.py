from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.urls import reverse
import requests

# NOTE: all "fetch_*" helpers below are placeholders to indicate
# "call Brain service here". Implement them by calling existing
# Brain endpoints only.

BRAIN_SERVICE_BASE_URL = "http://brain-srv:8000/api/v1/brain"

def is_jwt_authenticated(request) -> bool:
    """
    Helper: treat request as authenticated if JWTAuthMiddleware
    has attached `user_id` to the request.
    """
    return hasattr(request, "user_id")

def fetch_categories():
    """
    Call Brain proxy to fetch categories for the sell form.
    """
    try:
        resp = requests.get(f"{BRAIN_SERVICE_BASE_URL}/categories", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return []

def home(request, state_slug=None, district_slug=None,
         city_slug=None, locality_slug=None, category_slug_path=None):
    search_q = request.GET.get("q", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    filters = {
        "state_slug": state_slug,
        "district_slug": district_slug,
        "city_slug": city_slug,
        "locality_slug": locality_slug,
        # use last segment as category slug, if present
        "category_slug": category_slug_path.split("/")[-1]
        if category_slug_path else None,
        "location": search_q or None,  # or adjust to your search logic
        "min_price": min_price or None,
        "max_price": max_price or None,
    }
    params = {k: v for k, v in filters.items() if v is not None}

    try:
        resp = requests.get(
            f"{BRAIN_SERVICE_BASE_URL}/listings-with-images",
            params=params,
            timeout=5,
        )
        if resp.status_code == 200:
            listings = resp.json()
        else:
            listings = []
    except requests.RequestException:
        listings = []

    categories = []        # later: Brain /categories
    selected_location = {} # later: derive from slugs

    context = {
        "listings": listings,
        "categories": categories,
        "selected_location": selected_location,
        "filters": filters,
        "search_q": search_q,
        "min_price": min_price or "",
        "max_price": max_price or "",
    }
    return render(request, "listings/home.html", context)


def listing_grid_partial(request):
    """
    HTMX endpoint: returns only the listing grid fragment for filters/search.
    """
    # Extract filter params from query string (same as in home).
    # TODO: call Brain to fetch filtered listings.
    listings = []

    context = {
        "listings": listings,
        "is_authenticated": is_jwt_authenticated(request),
    }
    return render(request, "listings/_listing_grid.html", context)



def listing_detail(request, listing_slug):
    """
    Listing details page: fetch single listing + images via Brain and render.
    """
    try:
        listing_id = int(listing_slug)
    except ValueError:
        return HttpResponse("Invalid listing id", status=400)

    try:
        resp = requests.get(
            f"{BRAIN_SERVICE_BASE_URL}/listing/{listing_id}/with-images",
            timeout=5,
        )
    except requests.RequestException:
        return HttpResponse("Listing service unavailable", status=502)

    if resp.status_code != 200:
        return HttpResponse("Failed to fetch listing", status=resp.status_code)

    listing_data = resp.json()
    if not listing_data:
        return HttpResponse("Listing not found", status=404)

    images = listing_data.get("images", [])
    owner = listing_data.get("owner", {}) or {}
    owner_id = owner.get("id") or listing_data.get("owner_user_id")

    is_auth = is_jwt_authenticated(request)
    user_id = getattr(request, "user_id", None)
    is_owner = bool(is_auth and user_id and owner_id and int(user_id) == int(owner_id))

    full_phone = listing_data.get("phone", "") or ""
    phone_to_display = full_phone if is_auth else (full_phone or "**********")

    context = {
        "listing": {
            "slug": listing_slug,
            "title": listing_data.get("title", ""),
            "description": listing_data.get("description", ""),
            "price_display": listing_data.get("price_display") or str(listing_data.get("price", "")),
            "location_display": listing_data.get("location_display") or listing_data.get("location", ""),
            "images": [
                {"url": img.get("image") or img.get("url")}
                for img in images
                if img.get("image") or img.get("url")
            ],
            "owner": {
                "id": owner_id,
                "name": owner.get("name") or "Owner",
            },
            "phone": phone_to_display,
        },
        "is_owner": is_owner,
        "is_authenticated": is_auth,
    }
    return render(request, "listings/detail.html", context)



def sell_entrypoint(request):
    """
    Entry point for Sell button.
    If authenticated -> render sell modal with categories.
    Else -> show login modal.
    """
    if is_jwt_authenticated(request):
        categories = fetch_categories()
        return render(
            request,
            "listings/_sell_modal.html",
            {
                "user_id": getattr(request, "user_id", None),
                "categories": categories,
            },
        )

    context = {
        "next": reverse("huduku_ui:sell"),
        "mode": "login",
    }
    return render(request, "listings/_auth_modal.html", context)


def sell_form(request):
    """
    HTMX: return the sell / create-listing form fragment.

    Requires JWT-authenticated request; otherwise returns login modal.
    """
    if not is_jwt_authenticated(request):
        # not authenticated -> show login modal, come back here after login
        context = {
            "next": reverse("huduku_ui:sell_form"),
            "mode": "login",
        }
        return render(request, "listings/_auth_modal.html", context)

    user_id = getattr(request, "user_id", None)

    # Optional: fetch user info from auth_service if needed in the form
    user_info = {"id": user_id}
    try:
        resp = requests.get(
            f"{BRAIN_SERVICE_BASE_URL}/users/{user_id}",
            timeout=5,
        )
        if resp.status_code == 200:
            user_info = resp.json()
    except requests.RequestException:
        # ignore failure, continue with minimal user info
        pass

    categories = fetch_categories()
    return render(
        request,
        "listings/_sell_modal.html",
        {
            "user": user_info,
            "categories": categories,
        },
    )


@require_http_methods(["POST"])
def sell_submit(request):
    if not is_jwt_authenticated(request):
        return HttpResponse(status=401)

    user_id = getattr(request, "user_id", None)
    if user_id is None:
        return HttpResponse("Missing user id", status=401)

    title = request.POST.get("title", "").strip()
    category = request.POST.get("category", "").strip()  # should be numeric id from UI
    price = request.POST.get("price", "").strip()
    state_slug = request.POST.get("state_slug", "").strip()
    district_slug = request.POST.get("district_slug", "").strip()
    city_slug = request.POST.get("city_slug", "").strip()
    locality_slug = request.POST.get("locality_slug", "").strip()
    images = request.FILES.getlist("images")

    missing = []
    for field_name, value in [
        ("title", title),
        ("category", category),
        ("price", price),
        ("state_slug", state_slug),
        ("district_slug", district_slug),
        ("city_slug", city_slug),
        ("locality_slug", locality_slug),
    ]:
        if not value:
            missing.append(field_name)

    if not images:
        missing.append("images")

    if missing:
        return HttpResponse(
            "Missing required fields: " + ", ".join(missing),
            status=400,
        )

    try:
        payload = {
            "title": title,
            "category": int(category),
            "price": int(price),
            "state_slug": state_slug,
            "district_slug": district_slug,
            "city_slug": city_slug,
            "locality_slug": locality_slug,
            "is_active": True,
        }
    except ValueError:
        return HttpResponse("Invalid numeric value for category or price", status=400)

    try:
        resp = requests.post(
            f"{BRAIN_SERVICE_BASE_URL}/listing/create",
            json=payload,
            timeout=5,
            headers={
                "Authorization": f"Bearer {request.session.get('auth_token', '')}",
            },
        )
    except requests.RequestException:
        return HttpResponse("Listing service unavailable", status=502)

    if resp.status_code not in (200, 201):
        return HttpResponse(
            f"Failed to create listing: {resp.status_code} {resp.text}",
            status=400,
        )

    data = resp.json()
    listing_id = data.get("id")
    new_listing_slug = data.get("slug") or str(listing_id)
    if not listing_id:
        return HttpResponse("Missing listing id from Brain", status=500)

    # 2\) upload images via Brain image\-upload proxy
    for img in images:
        files = {"image": (img.name, img.read(), img.content_type)}
        try:
            img_resp = requests.post(
                f"{BRAIN_SERVICE_BASE_URL}/listing/{listing_id}/image/upload",
                files=files,
                timeout=10,
                headers={
                    "Authorization": f"Bearer {request.session.get('auth_token', '')}",
                },
            )
        except requests.RequestException:
            # you might want to log and continue; here just break
            break

        if img_resp.status_code not in (200, 201):
            # optional: handle partial failure
            break


    next_url = reverse(
        "huduku_ui:listing_detail",
        kwargs={"listing_slug": new_listing_slug},
    )
    response = HttpResponse(status=204)
    response["HX-Location"] = next_url
    return response


# ---------- Auth modals / actions ----------

def login_modal(request):
    """
    HTMX: login/register modal content.
    """
    return render(request, "listings/_auth_modal.html", {"mode": "login"})


def register_modal(request):
    """
    HTMX: register modal content.
    """
    return render(request, "listings/_auth_modal.html", {"mode": "register"})



@require_http_methods(["POST"])
def login_submit(request):
    """
    Handle login via Auth service and persist JWT token for subsequent requests.
    """
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    next_url = request.POST.get("next") or reverse("huduku_ui:home")

    if not email or not password:
        # re\-render login modal with error
        return render(
            request,
            "listings/_auth_modal.html",
            {"mode": "login", "error": "Email and password are required.", "next": next_url},
        )

    try:
        resp = requests.post(
            f"{BRAIN_SERVICE_BASE_URL}/login",
            json={"email": email, "password": password},
            timeout=5,
        )
    except requests.RequestException:
        return render(
            request,
            "listings/_auth_modal.html",
            {"mode": "login", "error": "Login service unavailable. Try again.", "next": next_url},
        )

    if resp.status_code != 200:
        return render(
            request,
            "listings/_auth_modal.html",
            {"mode": "login","error": "Invalid credentials.", "next": next_url},
        )

    data = resp.json()
    token = data.get("token")
    if not token:
        return render(
            request,
            "listings/_auth_modal.html",
            {"mode": "login", "error": "Login response missing token.", "next": next_url},
        )

    # save token for subsequent requests (Brain, Auth, etc.)
    request.session["auth_token"] = token

    # optionally: you can also store minimal user info if the auth service returns it
    # request.session["user_id"] = data.get("user_id")

    response = HttpResponse(status=204)
    response["HX-Location"] = next_url
    response.set_cookie(
        "auth_token",  # must match JWTAuthMiddleware cookie name
        token,
        httponly=True,
        secure=False,  # set True in production (HTTPS)
        samesite="Lax",
    )
    return response

@require_http_methods(["POST"])
def register_submit(request):
    """
    Handle register; delegate to Brain/Auth using only email and password.
    """
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    next_url = request.POST.get("next") or reverse("huduku_ui:home")

    if not email or not password:
        # re-render register modal with error
        return render(
            request,
            "listings/_auth_modal.html",
            {
                "mode": "register",
                "error": "Email and password are required.",
                "next": next_url,
                "form_values": {"email": email},
            },
        )

    try:
        resp = requests.post(
            f"{BRAIN_SERVICE_BASE_URL}/register",
            json={"email": email, "password": password},
            timeout=5,
        )
    except requests.RequestException:
        return render(
            request,
            "listings/_auth_modal.html",
            {
                "mode": "register",
                "error": "Registration service unavailable. Try again.",
                "next": next_url,
                "form_values": {"email": email},
            },
        )

    # Brain proxies auth-srv; on error we just surface its message
    if resp.status_code != 201:
        try:
            data = resp.json()
        except ValueError:
            data = {"detail": resp.text or "Registration failed."}

        error_msg = (
            data.get("detail")
            or data.get("message")
            or "Registration failed."
        )

        return render(
            request,
            "listings/_auth_modal.html",
            {
                "mode": "register",
                "error": error_msg,
                "next": next_url,
                "form_values": {"email": email},
            },
            status=resp.status_code,
        )

    # success: user is registered; you can either auto-login later or just redirect
    response = HttpResponse(status=204)
    response["HX-Location"] = next_url
    return response


def logout_view(request):
    """
    Log out via Brain/Auth and clear session.
    """
    # TODO: inform Brain/Auth if required, then Django logout.
    # django.contrib.auth.logout(request)
    return redirect("huduku_ui:home")


# ---------- Location selector partials ----------

def location_states(request):
    """
    HTMX: render list of states for selector/filter.
    """
    states = []
    try:
        resp = requests.get(f"{BRAIN_SERVICE_BASE_URL}/states", timeout=5)
        if resp.status_code == 200:
            states = resp.json()
    except requests.RequestException:
        pass

    return render(
        request,
        "listings/_location_selector.html",
        {
            "level": "state",
            "states": states,
        },
    )


def location_districts(request, state_slug):
    """
    HTMX: render districts for given state.
    """
    districts = []
    try:
        resp = requests.get(
            f"{BRAIN_SERVICE_BASE_URL}/states/{state_slug}/districts",
            timeout=5,
        )
        if resp.status_code == 200:
            districts = resp.json()
    except requests.RequestException:
        pass

    return render(
        request,
        "listings/_location_selector.html",
        {
            "level": "district",
            "state_slug": state_slug,
            "districts": districts,
        },
    )

def location_cities(request, state_slug, district_slug):
    """
    HTMX: render cities for given state+district.
    """
    cities = []
    try:
        resp = requests.get(
            f"{BRAIN_SERVICE_BASE_URL}/states/{state_slug}/districts/{district_slug}/cities",
            timeout=5,
        )
        if resp.status_code == 200:
            cities = resp.json()
    except requests.RequestException:
        pass

    return render(
        request,
        "listings/_location_selector.html",
        {
            "level": "city",
            "state_slug": state_slug,
            "district_slug": district_slug,
            "cities": cities,
        },
    )


def location_localities(request, state_slug, district_slug, city_slug):
    """
    HTMX: render localities for given state+district+city.
    """
    localities = []
    try:
        resp = requests.get(
            f"{BRAIN_SERVICE_BASE_URL}/states/{state_slug}/districts/"
            f"{district_slug}/cities/{city_slug}/localities",
            timeout=5,
        )
        if resp.status_code == 200:
            localities = resp.json()
    except requests.RequestException:
        pass

    selected_locality_slug = request.GET.get("locality")

    selected_locality = None
    if selected_locality_slug:
        selected_locality = next(
            (l for l in localities if l.get("slug") == selected_locality_slug),
            None,
        )

    return render(
        request,
        "listings/_location_selector.html",
        {
            "level": "locality",
            "state_slug": state_slug,
            "district_slug": district_slug,
            "city_slug": city_slug,
            "localities": localities,
            "selected_locality": selected_locality,
        },
    )


def filters_partial(request):
    """
    HTMX: return filters bar (categories, search, price, location selector).
    """
    # TODO: fetch categories and maybe current selection from Brain
    categories = []
    context = {"categories": categories}
    return render(request, "listings/_filters.html", context)


# ---------- Owner-only actions (edit, image ops) ----------

def listing_edit(request, listing_slug):
    """
    Edit listing page or modal (if owner).
    """
    if not is_jwt_authenticated(request):
        return HttpResponse(status=401)
    # TODO: fetch listing; verify owner via Brain; render form
    return HttpResponse("Edit listing UI here")


def listing_delete(request, listing_slug):
    """
    Owner delete listing; call Brain, then redirect to home.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    if not is_jwt_authenticated(request):
        return HttpResponse(status=401)

    # TODO: call Brain delete-listing
    return redirect("huduku_ui:home")


def listing_image_upload(request, listing_slug):
    """
    Owner image upload; call Brain, then return new image list fragment.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    if not is_jwt_authenticated(request):
        return HttpResponse(status=401)

    # TODO: send uploaded files to Brain; re-render images section
    return HttpResponse("Images section partial")


def listing_image_delete(request, listing_slug, image_id):
    """
    Owner image delete.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    if not is_jwt_authenticated(request):
        return HttpResponse(status=401)

    # TODO: call Brain delete-image; re-render images section
    return HttpResponse("Images section partial")