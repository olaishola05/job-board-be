from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import secrets
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    """
    Custom user manager for handling user creation with email as username
    """
    
    def _create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError('Invalid email format')
        
        email = self.normalize_email(email)
        
        # Generate username from email if not provided
        if 'username' not in extra_fields:
            username = email.split('@')[0]
            # Ensure username is unique
            counter = 1
            original_username = username
            while self.model.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            extra_fields['username'] = username
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        
        # Generate verification token for new users
        user.verification_token = secrets.token_urlsafe(50)
        
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)
        extra_fields.setdefault('role', 'user')
        
        return self._create_user(email, password, **extra_fields)
    
    def create_employer(self, email, password=None, **extra_fields):
        """Create and save an employer user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)
        extra_fields['role'] = 'employer'
        
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        """Allow authentication using email instead of username."""
        return self.get(**{f'{self.model.USERNAME_FIELD}__iexact': username})
    
    def get_active_users(self):
        """Get all active and verified users."""
        return self.filter(is_active=True, is_verified=True)
    
    def get_users_by_role(self, role):
        """Get users by role."""
        return self.filter(role=role, is_active=True)
    
    def get_employers(self):
        """Get all active employers."""
        return self.get_users_by_role('employer')
    
    def get_users(self):
        """Get all active job seekers."""
        return self.get_users_by_role('user')
    
    def get_admins(self):
        """Get all admin users."""
        return self.get_users_by_role('admin')
    
    def get_unverified_users(self, days_old=7):
        """Get unverified users older than specified days."""
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        return self.filter(
            is_verified=False,
            created_at__lt=cutoff_date
        )
    
    def cleanup_unverified_users(self, days_old=30):
        """Delete unverified users older than specified days."""
        users_to_delete = self.get_unverified_users(days_old)
        count = users_to_delete.count()
        users_to_delete.delete()
        return count