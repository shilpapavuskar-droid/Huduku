from django.db import models
from django.contrib.auth.models import User



class Users(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=10, blank=True)
    is_verified = models.BooleanField(default=False)


    def __str__(self):
        return self.user.email


