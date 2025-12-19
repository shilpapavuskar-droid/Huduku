from ninja import Schema ,Router
from django.contrib.auth.models import User
from pydantic import EmailStr, constr
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .services import register_user , update_user_profile

User = get_user_model()
router = Router(tags=["Users"])

class RegisterIn(Schema):
    email: EmailStr
    password: constr(min_length=8 , max_length=64)

class UserOut(Schema):
    id: int
    email: str


@router.post("/register", response=UserOut)
def register(request, payload: RegisterIn):
    user = register_user(
        email=payload.email,
        password=payload.password
    )
    return user

class UpdateUserProfileIN(Schema):

    first_name: constr(min_length=1 , max_length=100)
    last_name: constr(min_length=1 , max_length=100)
    phone: constr(min_length=10 , max_length=10)

class UpdateUserProfileOut(Schema):
    id: int
    first_name: str
    last_name: str
    phone: str


@router.post("/update_user_profile/{user_id}", response=UpdateUserProfileOut)
def update_user_profile_endpoint(request, payload: UpdateUserProfileIN, user_id: int):
    user = get_object_or_404(User, pk=user_id)
    user_profile = update_user_profile(
        id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone
    )
    return user_profile

class PasswordChangeIn(Schema):
    id: int
    current_password: constr(min_length=1)
    new_password: constr(min_length=8, max_length=64)
    new_password_confirm: constr(min_length=8, max_length=64)

class PasswordChangeOut(Schema):
    success: bool

@router.post("/users/change_password", response=PasswordChangeOut)
def change_password(request, payload: PasswordChangeIn):
    if payload.new_password != payload.new_password_confirm:
        raise HttpError(400, "New passwords do not match")
    user = get_object_or_404(User, pk=payload.id)
    if not user.check_password(payload.current_password):
        raise HttpError(400, "Invalid current password")
    user.set_password(payload.new_password)
    user.save(update_fields=["password"])
    return {"success": True}



class GetUser(Schema):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    is_verified: bool = False



@router.get("/users/{user_id}", response=GetUser)
def get_user(request, user_id: int):
    user = get_object_or_404(User, pk=user_id)
    return {"id": user.id,
            "email": user.email,
            "first_name": user.profile.first_name,
            "last_name": user.profile.last_name,
            "phone": user.profile.phone,
            "is_verified": user.profile.is_verified}

#TODO: forgot password.