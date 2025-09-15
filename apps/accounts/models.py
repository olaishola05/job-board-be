from django.db import models

from django.contrib.auth.models import AbstractUser
from uuid import uuid4


class User(AbstractUser):
    """
    Extended user model with role-based access control
    """
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("employer", "Employer"),
        ("user", "User"),
    )

    email = models.EmailField(unique=True)
    user = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return f"{self.email} ({self.role})"
