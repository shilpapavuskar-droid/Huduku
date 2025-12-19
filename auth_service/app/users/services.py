from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

def register_user(email: str, password: str):
    if not email:
        raise ValidationError("Email is required")

    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already registered")

    user = User.objects.create_user(
        username=email,   # 👈 username = email
        email=email,
        password=password
    )

    return user

def update_user_profile(id: int, first_name: str, last_name: str, phone: str):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise ValidationError("User does not exist")

    profile = user.profile  # Accessing related UserProfile via related_name

    profile.first_name = first_name
    profile.last_name = last_name
    profile.phone = phone
    profile.save()

    return profile