from ninja import Schema
from ninja import Router
from django.contrib.auth.models import User
from .services import register_user , update_user_profile
from pydantic import EmailStr, constr

class RegisterIn(Schema):
    email: EmailStr
    password: constr(min_length=8 , max_length=64)

class UserOut(Schema):
    id: int
    email: str

router = Router(tags=["Users"])
@router.post("/register", response=UserOut)
def register(request, payload: RegisterIn):
    user = register_user(
        email=payload.email,
        password=payload.password
    )
    return user

class UpdateUserProfileIN(Schema):
    id: int
    first_name: constr(min_length=1 , max_length=100)
    last_name: constr(min_length=1 , max_length=100)
    phone: constr(min_length=10 , max_length=10)

class UpdateUserProfileOut(Schema):
    id: int
    first_name: str
    last_name: str
    phone: str


@router.post("/update_user_profile", response=UpdateUserProfileOut)
def update_user_profile_endpoint(request, payload: UpdateUserProfileIN):
    user_profile = update_user_profile(
        id=payload.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone
    )
    return user_profile