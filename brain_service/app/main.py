from fastapi import FastAPI, HTTPException, Path,UploadFile ,Request, Query ,File
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional


app = FastAPI()

AUTH_URL = "http://auth-srv:8000/api/v1"
LISTING_URL = "http://listing-srv:8000/api/v1"
REGION_URL = "http://region-srv:5000"

origins = [
    "http://localhost:3000",   # React dev
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # or ["*"] during dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/categories")
async def get_categories():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{LISTING_URL}/category")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.get("/listings")
async def get_all_listings():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{LISTING_URL}/listings")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.get("/user/{user_id}/listings")
async def get_user_listings(user_id: int):
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(f"{AUTH_URL}/users/{user_id}")
        if user_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        user = user_resp.json()

        listings_resp = await client.get(f"{LISTING_URL}/listings?user_id={user_id}")
        if listings_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Listings not found")
        listings = listings_resp.json()

    return {"user": user, "listings": listings}


class ListingImageOut(BaseModel):
    id: int
    listing_id: int
    image: str
    created_at: str  # or datetime


class ListingWithImagesOut(BaseModel):
    id: int
    title: str
    owner_user_id: int
    category_id: int
    price: float
    location: str
    is_active: bool
    created_at: str
    updated_at: str
    images: List[ListingImageOut] = []

@app.get(
    "/listings-with-images",
    response_model=List[ListingWithImagesOut],
)
async def get_listings_with_images(
    location: Optional[str] = Query(default=None),
    category: Optional[int] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    state_slug: Optional[str] = Query(default=None),
    district_slug: Optional[str] = Query(default=None),
    city_slug: Optional[str] = Query(default=None),
    locality_slug: Optional[str] = Query(default=None),
    category_slug: Optional[str] = Query(default=None),
):
    params: dict = {}
    if location is not None:
        params["location"] = location
    if category is not None:
        params["category"] = category
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if user_id is not None:
        params["user_id"] = user_id
    if state_slug:
        params["state_slug"] = state_slug
    if district_slug:
        params["district_slug"] = district_slug
    if city_slug:
        params["city_slug"] = city_slug
    if locality_slug:
        params["locality_slug"] = locality_slug
    if category_slug:
        params["category_slug"] = category_slug

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{LISTING_URL}/listings", params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        listings = resp.json()

        results: List[ListingWithImagesOut] = []
        for l in listings:
            images_resp = await client.get(
                f"{LISTING_URL}/listing/{l['id']}/images/"
            )
            images_json = images_resp.json() if images_resp.status_code == 200 else []
            images = [ListingImageOut(**img) for img in images_json]
            results.append(ListingWithImagesOut(**l, images=images))
    return results

@app.post("/listing/{listing_id}/image/upload", response_model=ListingImageOut)
async def upload_listing_image(
    listing_id: int,
    request: Request,
    image: UploadFile = File(...),
):
    user = await verify_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue")

    # forward multipart form data to listing service
    async with httpx.AsyncClient() as client:
        files = {
            "image": (image.filename, await image.read(), image.content_type),
        }
        resp = await client.post(
            f"{LISTING_URL}/listing/{listing_id}/image/upload",
            files=files,
            headers={},  # auth is already done at brain; listing service expects no auth
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()



class RegisterRequest(BaseModel):
    email: str
    password: str

@app.post("/register")
async def register(data: RegisterRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{AUTH_URL}/register", json=data.dict())
        if resp.status_code != 201:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
async def login(data: LoginRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{AUTH_URL}/login", json=data.dict())
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()


class ChangePasswordRequest(BaseModel):
    id: int
    current_password: str
    new_password: str
    new_password_confirm: str

@app.post("/users/change_password")
async def change_password(data: ChangePasswordRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{AUTH_URL}/users/change_password", json=data.dict())
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()


class UpdateUserProfileRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str


@app.post("/update_user_profile")
async def update_user_profile(request:Request, data: UpdateUserProfileRequest):
    user = await verify_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue")
    user_id = user.get("user_id")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{AUTH_URL}/update_user_profile/{user_id}",
            json=data.dict()
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

class CreateListingRequest(BaseModel):
    title: str
    category: int
    price: float
    state_slug: str
    district_slug: str
    city_slug: str
    locality_slug: str  # most specific
    is_active: bool = True

@app.post("/listing/create")
async def create_listing(request: Request, data: CreateListingRequest):
    user = await verify_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue")
    user_id = user.get("user_id")
    location_path = (
        f"{data.state_slug}/"
        f"{data.district_slug}/"
        f"{data.city_slug}/"
        f"{data.locality_slug}"
    )
    payload = {
        "user_id": user_id,
        "title": data.title,
        "category": data.category,
        "price": data.price,
        "locality_slug": data.locality_slug,
        "location": location_path,
        "is_active": data.is_active,
    }
    # listing service will store locality_slug as location-or separate column
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{LISTING_URL}/listing/create", json=payload)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()



class UpdateListingRequest(BaseModel):
    title: str | None = None
    category: int | None = None
    price: float | None = None
    location: str | None = None
    is_active: bool | None = None

@app.put("/listing/{listing_id}")
async def update_listing(listing_id: int, request: Request, data: UpdateListingRequest):
    user = await verify_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue")
    user_id = user.get("user_id")
    is_staff = user.get("is_staff", False)

    async with httpx.AsyncClient() as client:
        # Fetch the listing to check ownership
        resp = await client.get(f"{LISTING_URL}/listing/{listing_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Listing not found")
        listing = resp.json()
        if listing["owner_user_id"] != user_id and not is_staff:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Forward the update request
        update_resp = await client.put(
            f"{LISTING_URL}/listing/{listing_id}",
            json=data.dict(exclude_unset=True)
        )
        if update_resp.status_code != 200:
            raise HTTPException(status_code=update_resp.status_code, detail=update_resp.text)
        return update_resp.json()

@app.delete("/listing/{listing_id}")
async def delete_listing(listing_id: int, request: Request):
    user = await verify_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue")

    user_id = user.get("user_id")
    is_staff = user.get("is_staff", False)

    async with httpx.AsyncClient() as client:
        # fetch listing to verify ownership
        resp = await client.get(f"{LISTING_URL}/listing/{listing_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Listing not found")

        listing = resp.json()
        if listing["owner_user_id"] != user_id and not is_staff:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # forward delete to listing service
        delete_resp = await client.delete(f"{LISTING_URL}/listing/{listing_id}")
        if delete_resp.status_code != 200:
            raise HTTPException(
                status_code=delete_resp.status_code,
                detail=delete_resp.text,
            )
        return delete_resp.json()

async def verify_user(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTH_URL}/users/verify-token",
            headers={"Authorization": token},
            timeout=5
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.json()

@app.get("/states")
async def get_states():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{REGION_URL}/states")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()


@app.get("/states/{state_slug}/districts")
async def get_districts(state_slug: str):
    async with httpx.AsyncClient() as client:
        state_resp = await client.get(
            f"{REGION_URL}/states",
            params={"slug": state_slug},
        )
        if state_resp.status_code != 200:
            raise HTTPException(status_code=state_resp.status_code, detail=state_resp.text)
        states = state_resp.json()
        if not states:
            raise HTTPException(status_code=404, detail="State not found")

        state_code = states[0]["code"]

        dist_resp = await client.get(
            f"{REGION_URL}/states/{state_code}/districts"
        )
        if dist_resp.status_code != 200:
            raise HTTPException(status_code=dist_resp.status_code, detail=dist_resp.text)
        return dist_resp.json()


@app.get("/states/{state_slug}/districts/{district_slug}/cities")
async def get_cities(state_slug: str, district_slug: str):
    async with httpx.AsyncClient() as client:
        state_resp = await client.get(
            f"{REGION_URL}/states",
            params={"slug": state_slug},
        )
        if state_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="State not found")
        states = state_resp.json()
        if not states:
            raise HTTPException(status_code=404, detail="State not found")
        state_code = states[0]["code"]

        dist_resp = await client.get(
            f"{REGION_URL}/states/{state_code}/districts"
        )
        if dist_resp.status_code != 200:
            raise HTTPException(status_code=dist_resp.status_code,
                                detail=dist_resp.text)
        districts = dist_resp.json()
        district = next((d for d in districts if d["slug"] == district_slug),
                        None)
        if not district:
            raise HTTPException(status_code=404, detail="District not found")

        city_resp = await client.get(
            f"{REGION_URL}/states/{state_code}/districts/{district['code']}/cities"
        )
        if city_resp.status_code != 200:
            raise HTTPException(status_code=city_resp.status_code,
                                detail=city_resp.text)
        return city_resp.json()


@app.get(
    "/states/{state_slug}/districts/{district_slug}/cities/{city_slug}/localities"
)
async def get_localities(
    state_slug: str,
    district_slug: str,
    city_slug: str,
):
    async with httpx.AsyncClient() as client:
        state_resp = await client.get(
            f"{REGION_URL}/states",
            params={"slug": state_slug},
        )
        if state_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="State not found")
        states = state_resp.json()
        if not states:
            raise HTTPException(status_code=404, detail="State not found")
        state_code = states[0]["code"]

        dist_resp = await client.get(
            f"{REGION_URL}/states/{state_code}/districts"
        )
        if dist_resp.status_code != 200:
            raise HTTPException(status_code=dist_resp.status_code,
                                detail=dist_resp.text)
        districts = dist_resp.json()
        district = next((d for d in districts if d["slug"] == district_slug),
                        None)
        if not district:
            raise HTTPException(status_code=404, detail="District not found")

        city_resp = await client.get(
            f"{REGION_URL}/states/{state_code}/districts/{district['code']}/cities"
        )
        if city_resp.status_code != 200:
            raise HTTPException(status_code=city_resp.status_code,
                                detail=city_resp.text)
        cities = city_resp.json()
        city = next((c for c in cities if c["slug"] == city_slug), None)
        if not city:
            raise HTTPException(status_code=404, detail="City not found")

        loc_resp = await client.get(
            f"{REGION_URL}/states/{state_code}/districts/{district['code']}/cities/{city['code']}/locality"
        )
        if loc_resp.status_code != 200:
            raise HTTPException(status_code=loc_resp.status_code,
                                detail=loc_resp.text)
        return loc_resp.json()