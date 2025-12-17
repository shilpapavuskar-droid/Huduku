from typing import List,Optional
from typing import List,Optional
import uuid
from ninja import Router,Schema
from .models import Category, Listing, ListingMedia, Review, Favorite
from ninja.errors import HttpError
from ninja import Schema
from django.shortcuts import get_object_or_404
import  datetime


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
    owner_user_id: int
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
def get_listings(request):
    listings = Listing.objects.filter(is_active=True)
    return list(listings)

@router.post("/listing/create", response=ListingOut)
def create_listing(request, data: ListingIn):

    # Get category instance
    category = get_object_or_404(Category,id=data.category)
   # create listing
    data.category =category
    listing = Listing.objects.create(**data.dict())
    return listing
# #
# #
@router.get("/listing/{listing_id}", response=ListingOut)
def get_listing(request, listing_id: int):
    return get_object_or_404(Listing, id=listing_id)
#
#
@router.put("/listing/{listing_id}", response=ListingOut)
def update_listing(request, listing_id:int , data: ListingIn):
    listing = get_object_or_404(Listing, id=listing_id)


    #update fields individually
    if data.title:
        listing.title = data.title
    if data.owner_user_id:
        listing.owner_user_id = data.owner_user_id
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
    listing.delete()
    return {"success": True}
#
# # #-------------------
# #ListingMedia
# #---------------------
class ListingMediaIn(Schema):
    listing: int     # listing_id
    media_id: int     # external storage id (S3, cloud)
    type: str               # e.g., "image", "video"


class ListingMediaOut(Schema):
    id: int
    listing: int
    media_id: int
    type: str

@router.post("/media/create", response=ListingMediaOut, tags=["media"])
def create_media(request, data: ListingMediaIn):
    listing = get_object_or_404(Listing, id=data.listing_id)

    media = ListingMedia.objects.create(
        listing=listing,
        media_id=data.media_id,
        type=data.type
    )

    return media
#
@router.get("/media/list/{listing_id}", response=list[ListingMediaOut], tags=["media"])
def list_media(request, listing_id: int):
    return ListingMedia.objects.filter(listing_id=listing_id)

@router.get("/media/{media_id}", response=ListingMediaOut, tags=["media"])
def get_media(request, media_id: int):
    return get_object_or_404(ListingMedia, id=media_id)

#
@router.put("/media/{media_id}", response=ListingMediaOut, tags=["media"])
def update_media(request, media_id: int, data: ListingMediaIn):
    media = get_object_or_404(ListingMedia, id=media_id)
    listing = get_object_or_404(Listing, id=data.listing_id)

    media.listing = listing
    media.media_id = data.media_id
    media.type = data.type
    media.save()

    return media
#
@router.delete("/media/{media_id}", tags=["media"])
def delete_media(request, media_id: int):
    media = get_object_or_404(ListingMedia, id=media_id)
    media.delete()

    return {"success": True}

# #
# # # #-----------------
# # #Review endpoints
# # #------------------
# class ReviewIn(Schema):
#     listing: int       # listing_id
#     user_id: int        # reviewer
#     rating: int
#     comment: Optional[str] = None
# #
# #
# class ReviewOut(Schema):
#     id: int
#     listing: int
#     user_id: int
#     rating: int
#     comment: Optional[str]
#     created_at: datetime
#
#
#
# #
# @router.get("/reviews/{listing_id}", response=List[ReviewOut])
# def get_reviews(request, listing_id: int):
#     return Review.objects.filter(listing_id=listing_id)
#
#
# @router.post("/review/create", response=ReviewOut)
# def create_review(request, data: ReviewIn):
#     review = Review.objects.create(**data.dict())
#     return review
#
#
# # #--------------------
# # #Favotite Endpoints
# # #--------------------
# class FavoriteIn(Schema):
#     user_id :int
#     listing:int
#
# class FavoriteOut(Schema):
#     id: int
#     user_id: int
#     listing_id: int
#     created_at: datetime
#
#
#
#
# @router.post("/favorite/add", response=FavoriteOut)
# def add_favorite(request, data: FavoriteIn):
#     favorite = Favorite.objects.create(
#         user_id=data.user_id,
#         listing_id=data.listing_id
#     )
#     return favorite
#
#
# @router.get("/favorites/{user_id}", response=List[FavoriteOut])
# def list_favorites(request, user_id: int):
#     return list(Favorite.objects.filter(user_id=user_id))
#
#
#
#
# @router.delete("/favorite/{favorite_id}")
# def delete_favorite(request, favorite_id: int):
#     fav = get_object_or_404(Favorite,id=favorite_id)
#     fav.delete()
#     return {"success": True}
#
#

