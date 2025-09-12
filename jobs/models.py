from django.db import models
from django.contrib.auth.models import AbstractUser
from uuid import uuid4


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("employer", "Employer"),
        ("user", "User"),
    )

    email = models.EmailField(unique=True)
    user = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    onboarding_complete = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    def __str__(self):
        return self.email
