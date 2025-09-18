from django.db import models
from django.contrib.auth.models import AbstractUser
from uuid import uuid4

from jsonschema import ValidationError
from .utils import phone_regex
from django.utils import timezone
import secrets
from datetime import timedelta
from .managers import UserManager
from .utils import validate_linkedin_url, validate_github_url
from django.core.validators import MinValueValidator, MaxValueValidator

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
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True
    )
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token_created = models.DateTimeField(blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token_created = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=100, blank=True, null=True)
    activation_token_created = models.DateTimeField(blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_password_change = models.DateTimeField(auto_now_add=True, null=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager() # type: ignore
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_active']),
            models.Index(fields=['account_locked_until']),
        ]

    def __str__(self):
         return f"{self.email} ({self.role})"
       
    @property
    def is_account_locked(self):
      """Check if the account is currently locked."""
      if self.account_locked_until:
          return timezone.now() < self.account_locked_until
      return False
    
    def lock_account(self, duration_minutes=30):
      self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
      self.save(update_fields=['account_locked_until'])
      
    def unlock_account(self):
      """Unlock the account & reset failed login attempts."""
      self.account_locked_until = None
      self.failed_login_attempts = 0
      self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
      
    def increment_failed_attempts(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_attempts(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])
    
    def generate_verification_token(self):
        """Generate email verification token"""
        self.verification_token = secrets.token_urlsafe(50)
        self.verification_token_created = timezone.now()
        self.save(update_fields=['verification_token', 'verification_token_created'])
        return self.verification_token
    
    def generate_password_reset_token(self):
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(50)
        self.password_reset_token_created = timezone.now()
        self.save(update_fields=['password_reset_token', 'password_reset_token_created'])
        return self.password_reset_token
    
    def generate_activation_token(self):
        """Generate account activation token"""
        self.activation_token = secrets.token_urlsafe(50)
        self.activation_token_created = timezone.now()
        self.save(update_fields=['activation_token', 'activation_token_created'])
        return self.activation_token
    
    def is_token_valid(self, token_type, token_value, max_age_hours=24):
        """Check if a token is valid and not expired"""
        if token_type == 'verification':
            stored_token = self.verification_token
            created_time = self.verification_token_created
        elif token_type == 'password_reset':
            stored_token = self.password_reset_token
            created_time = self.password_reset_token_created
        elif token_type == 'activation':
            stored_token = self.activation_token
            created_time = self.activation_token_created
        else:
            return False
        
        if not stored_token or stored_token != token_value:
            return False
        
        if not created_time:
            return False
          
        expiry_time = created_time + timezone.timedelta(hours=max_age_hours)
        return timezone.now() <= expiry_time
    
    def clear_token(self, token_type):
        """Clear specified token after use"""
        if token_type == 'verification':
            self.verification_token = None
            self.verification_token_created = None
            self.save(update_fields=['verification_token', 'verification_token_created'])
        elif token_type == 'password_reset':
            self.password_reset_token = None
            self.password_reset_token_created = None
            self.save(update_fields=['password_reset_token', 'password_reset_token_created'])
        elif token_type == 'activation':
            self.activation_token = None
            self.activation_token_created = None
            self.save(update_fields=['activation_token', 'activation_token_created'])
    
    def verify_email(self):
        """Mark email as verified and activate account"""
        self.is_verified = True
        self.is_active = True
        self.clear_token('verification')
        self.save(update_fields=['is_verified', 'is_active'])
    
    def deactivate_account(self):
        """Deactivate user account"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def activate_account(self):
        """Activate user account"""
        self.is_active = True
        self.save(update_fields=['is_active'])
        
    def cleanup_unverified_users(self, days_old=30):
        """Class method to delete unverified users older than specified days"""
        cutoff_date = timezone.now() - timedelta(days=days_old)
        unverified_users = User.objects.filter(
            is_verified=False,
            created_at__lt=cutoff_date
        )
        count = unverified_users.count()
        unverified_users.delete()
        return count
      
    def get_full_name(self):
        """Return full name or email if names not available"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def is_employer(self):
        """Check if user is an employer"""
        return self.role == 'employer'
    
    def is_user(self):
        """Check if user is a job seeker"""
        return self.role == 'user'
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin' or self.is_superuser
        
class Profile(models.Model):
    """
    Extended profile information for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True, validators=[validate_linkedin_url])
    github_url = models.URLField(blank=True, null=True, validators=[validate_github_url])
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True, validators=[MaxValueValidator(50)])
    experience_years = models.PositiveIntegerField(blank=True, null=True)
    salary_expectation = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True, help_text="Available for job opportunities")
    visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('employers_only', 'Employers Only'),
        ],
        default='public'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'
        indexes = [
            models.Index(fields=['location', 'is_available']),
            models.Index(fields=['experience_years', 'is_available']),
            models.Index(fields=['visibility', 'is_available']),
            models.Index(fields=['updated_at']),
        ]
    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"
    
    def clean(self):
        """Custom validation"""
        if self.salary_expectation and self.salary_expectation < 0:
            raise ValidationError('Salary expectation cannot be negative')
    
    @property
    def completion_percentage(self):
        """Calculate profile completion percentage"""
        fields = ['bio', 'location', 'avatar', 'resume']
        completed = sum(1 for field in fields if getattr(self, field))
        return int((completed / len(fields)) * 100)
    
    def get_skills_by_category(self):
        """Return skills grouped by category"""
        return self.skills.select_related('category').order_by('category__name', 'name')
  
      
class RefreshToken(models.Model):
    """
    Custom refresh token model for JWT authentication
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)
    
    # Device/session tracking
    device_info = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'refresh_tokens'
        indexes = [
            models.Index(fields=['user', 'is_revoked']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Refresh token for {self.user.email}"
    
    @property
    def is_expired(self):
        """Check if token is expired"""
        return timezone.now() >= self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_expired and not self.is_revoked
    
    def revoke(self):
        """Revoke the token"""
        self.is_revoked = True
        self.save(update_fields=['is_revoked'])
    
    @classmethod
    def create_token(cls, user, device_info=None, ip_address=None, user_agent=None):
        """Create a new refresh token"""
        token = secrets.token_urlsafe(50)
        expires_at = timezone.now() + timedelta(days=7)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired tokens"""
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
class LoginAttempt(models.Model):
    """
    Track login attempts for security monitoring
    """
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField()
    failure_reason = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        indexes = [
            models.Index(fields=['email', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt for {self.email} from {self.ip_address}"