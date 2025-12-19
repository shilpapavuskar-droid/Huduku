from django.contrib import admin
from .models import Users


# ------------------------------
# UserProfile Admin
# ------------------------------

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "is_verified","first_name", "last_name")
    search_fields = ("user__username", "user__email")

