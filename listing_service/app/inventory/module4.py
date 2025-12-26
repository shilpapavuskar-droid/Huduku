from email.mime import image
from typing import List,Optional
from typing import List,Optional
import uuid
from ninja import Router,Schema
from .models import Category, Listing, Review, Favorite, ListingImage
from ninja.errors import HttpError
from ninja import Schema
from django.shortcuts import get_object_or_404
import  datetime
from ninja import  File
from ninja.files import UploadedFile
from ninja import Query
from django.db import IntegrityError
from clients.auth_client import verify_user

router = Router()
MEDIA_URL = '/media/'

#------------------------------
#Category end-points
#------------------------------
class CategoryIn(Schema):
    name: str
    slug: str
    parent: Optional[int] =None

class CategoryOut(Schema):
    id: int
    name: str
    slug: str
    parent_id: Optional[int]


@router.get(
    "/category",
    tags=["module4"],
    response=List[CategoryOut],
    summary="List all categories",
    description="List all categories"
)
def get_categories(request):
    return Category.objects.all()

@router.post("/category/create", tags=["module4"],summary="create new category" )
def create_category(request, data: CategoryIn):
    if data.parent is not None:
        parent = get_object_or_404(Category, id=data.parent)
        data.parent = parent
    category = Category.objects.create(**data.dict())
    return True


@router.get("/category/{category_id}", response=CategoryOut)
def get_category(request, category_id: int):
    return get_object_or_404(Category, id=category_id)


@router.put("/category/{category_id}", response=CategoryOut)
def update_category(request, category_id: int, data: CategoryIn):
    category = get_object_or_404(Category, id=category_id)
    if data.parent is not None:
        data.parent = category

    for attr, value in data.dict().items():
        setattr(category, attr, value)

    category.save()
    return category

@router.delete("/category/{category_id}")
def delete_category(request, category_id: int):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return {"success": True}



#---------------------------
# #Listing endpoints
# #---------------------------
#
class ListingIn(Schema):
    title: str
    category: int           # send category_id
    price: float
    location: str
    is_active: Optional[bool] = True


class ListingOut(Schema):
    id: int
    title: str
    owner_user_id: int
    category_id: int
    price: float
    location: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


@router.get("/listings", response=List[ListingOut])
def get_listings(request,location: Optional[str] = Query(None),
    category: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None)):
    qs = Listing.objects.filter(is_active=True)

    if location:
        qs = qs.filter(location__icontains=location)

    if category:
        qs = qs.filter(category_id=category)

    if min_price is not None:
        qs = qs.filter(price__gte=min_price)

    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    return list(qs)

@router.post("/listing/create", response=ListingOut)
def create_listing(request, data: ListingIn):
    user = verify_user(request)
    if not user:
        raise HttpError(401, "Unauthorized")
    # Get category instance
    category = get_object_or_404(Category,id=data.category)
    # create listing
    data.category =category
    listing = Listing.objects.create(
        title=data.title,
        category=category,
        price=data.price,
        location=data.location,
        is_active=data.is_active,
        owner_user_id=user["user_id"]
    )
    return listing
# #
# #
@router.get("/listing/{listing_id}", response=ListingOut)
def get_listing(request, listing_id: int):
    return get_object_or_404(Listing, id=listing_id)
#

class ListingUpdateIn(Schema):
    title: Optional[str] = None
    category: Optional[int] = None
    price: Optional[float] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
#
@router.put("/listing/{listing_id}", response=ListingOut)
def update_listing(request, listing_id:int , data: ListingUpdateIn):
    listing = get_object_or_404(Listing, id=listing_id)
    user = verify_user(request)
    user_id = user.get("user_id")
    if user_id != listing.owner_user_id and not user.get("is_staff", False):
        raise HttpError(401, "Unauthorized")


    #update fields individually
    if data.title:
        listing.title = data.title
    if data.category:
        listing.category = get_object_or_404(Category,id=data.category)
    if data.price is not None:
        listing.price = data.price
    if data.location:
        listing.location = data.location
    if data.is_active is not None:
        listing.is_active = data.is_active

    listing.save()
    return listing
#
#
@router.delete("/listing/{listing_id}")
def delete_listing(request, listing_id: int):
    listing = get_object_or_404(Listing, id=listing_id)
    user = verify_user(request)
    if user.get("user_id") != listing.owner_user_id and not user.get("is_staff", False):
        raise HttpError(401, "Unauthorized")
    listing.delete()
    return {"success": True}
#
# # #-------------------
# #ListingImages
# #---------------------
class ListingImageIn(Schema):
    listing_id: int



class ListingImageOut(Schema):
    id: int
    listing_id: int
    image: str
    created_at: datetime.datetime

@router.post("/listing/{listing_id}/image/upload", response=ListingImageOut )
def upload_listing_image(request, listing_id: int,image:UploadedFile = File(...)
                         ):
    listing = get_object_or_404(Listing, id=listing_id)
    user = verify_user(request)
    if user.get("user_id") != listing.owner_user_id:
        raise HttpError(401, "Unauthorized")

    listing_image = ListingImage.objects.create(
        listing=listing,
        image=image
    )

    return {
        "id": listing_image.id,
        "listing_id": listing.id,
        "image": listing_image.image.url,
        "created_at": listing_image.created_at,
    }
#
@router.get("/listing/{listing_id}/images/", response=List[ListingImageOut])
def get_listing_images(request, listing_id: int):
    images = ListingImage.objects.filter(listing_id=listing_id)

    return [
         {
             "id": img.id,
             "listing_id": img.listing_id,
             "image":img.image.url,
             "created_at": img.created_at,
         }
       for img in images
   ]

@router.delete("/listing/{listing_id}/images/")
def delete_listing_image(request, listing_id : int):
    listing = get_object_or_404(Listing, id=listing_id)
    user = verify_user(request)
    if user.get("user_id") != listing.owner_user_id and not user.get("is_staff", False):
        raise HttpError(401, "Unauthorized")
    deleted_count, _ = ListingImage.objects.filter(listing=listing).delete()
    return {
        "success": True,
        "deleted_images": deleted_count
    }


@router.delete("/listing/{listing_id}/image/{image_id}")
def delete_single_listing_image(request, listing_id: int, image_id: int):
    listing = get_object_or_404(Listing, id=listing_id)
    user = verify_user(request)
    if user.get("user_id") != listing.owner_user_id and not user.get("is_staff", False):
        raise HttpError(401, "Unauthorized")
    image = get_object_or_404(
        ListingImage,
        id=image_id,
        listing_id=listing_id
    )
    image.delete()
    return {"success": True}

# @router.get("/media/{media_id}", response=ListingMediaOut, tags=["media"])
# def get_media(request, media_id: int):
#     return get_object_or_404(ListingMedia, id=media_id)
#
# #
# @router.put("/media/{media_id}", response=ListingImageOut, tags=["media"])
# def update_media(request, media_id: int, data: ListingMediaIn):
#     media = get_object_or_404(ListingMedia, id=media_id)
#     listing = get_object_or_404(Listing, id=data.listing_id)
#
#     media.listing = listing
#     media.media_id = data.media_id
#     media.type = data.type
#     media.save()
#
#     return media
# #





# # #--------------------
# # #Favotite Endpoints
# # #--------------------
class FavoriteIn(Schema):
    user_id :int
    listing_id:int

class FavoriteOut(Schema):
    id: int
    user_id: int
    listing_id: int
    created_at: datetime.datetime




@router.post("/favorite/add", response=FavoriteOut)
def add_favorite(request, data: FavoriteIn):
    user = get_object_or_404(User,id=data.user_id)
    listing = get_object_or_404(Listing, id=data.listing_id)

    try:
        favorite = Favorite.objects.create(
        user=user,
        listing=listing
    )
    except IntegrityError:
        return{
            "error": True,
            "message":"Already favorited"
        }
    return {
        "id": favorite.id,
        "user_id": favorite.user.id,
        "listing_id": favorite.listing.id,
     }


@router.get("/favorites/{user_id}", response=List[FavoriteOut])
def list_favorites(request, user_id: int):
    return list(
        Favorite.objects.filter(user_id=user_id).select_related("listing")

   )

@router.delete("/favorite/{favorite_id}")
def delete_favorite(request, favorite_id: int):
    try:
        fav = Favorite.objects.get(id=favorite_id)
    except Favorite.DoesNotExist:
        return{"error": True,"message":"Favorite not found "}
    fav.delete()
    return {"success": True}

# # #------------------

