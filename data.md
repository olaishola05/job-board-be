# Base prompt

Use Django and Django REST Framework and viewsets.ModelViewSet for the views, serializers.Serializer for the serializers, ensuring security best practices and scalability. Don't give me verbose code and I want the code to be compact and efficient and use informations provided in the context.

Develop a complete company management system with:

- Company profile creation and management
- Company verification system for trusted employers
- Company-specific job postings management
- Company analytics dashboard data
- Company search and filtering
- Company logo and media upload handling
- Industry association and categorization
- Company size and founding year tracking
- Company location management with geocoding
- Company following/subscription system for job seekers
- Admin approval workflow for new companies
- Company performance metrics and reporting
- API versioning and proper HTTP status codes
- Write tests for the views and the serializers

Permissions:

```python
# apps.core.permissions
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'applicant'):
            return obj.applicant == request.user
        
        return False

class IsEmployerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for employer-only actions
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.is_employer()

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission for admin-only actions
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.is_admin()

# apps.accounts.permissions
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from functools import wraps
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from rest_framework import status


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsAdminUser(BasePermission):
    """
    Permission for admin users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, "role", None) == "admin"
        )


class IsEmployerUser(BasePermission):
    """
    Permission for employer users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'employer'
        )


class IsJobSeekerUser(BasePermission):
    """
    Permission for job seeker users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'user'
        )


class IsEmployerOrAdmin(BasePermission):
    """
    Permission for employer or admin users
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['employer', 'admin']
        )


class IsVerifiedUser(BasePermission):
    """
    Permission for verified users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_verified
        )


class IsActiveUser(BasePermission):
    """
    Permission for active users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_active
        )


class IsOwner(BasePermission):
    """
    Permission to check if user is owner of the object
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        return False


class CanManageUsers(BasePermission):
    """
    Permission for users who can manage other users (admin only)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin' and
            request.user.is_staff
        )


class CanViewUserProfile(BasePermission):
    """
    Permission to view user profiles - own profile or admin
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user == request.user if hasattr(obj, 'user') else obj == request.user

def admin_required(view_func):
    """
    Decorator for views that require admin role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def employer_required(view_func):
    """
    Decorator for views that require employer role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role != 'employer':
            return JsonResponse({'error': 'Employer access required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def job_seeker_required(view_func):
    """
    Decorator for views that require job seeker or user role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role != 'user':
            return JsonResponse({'error': 'user access required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def verified_required(view_func):
    """
    Decorator for views that require verified email
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_verified:
            return JsonResponse({'error': 'Email verification required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def active_required(view_func):
    """
    Decorator for views that require active account
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_active:
            return JsonResponse({'error': 'Account activation required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def role_required(*allowed_roles):
    """
    Decorator for views that require specific roles
    Usage: @role_required('admin', 'employer')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            if request.user.role not in allowed_roles:
                return JsonResponse({
                    'error': f'Access denied. Required roles: {", ".join(allowed_roles)}'
                }, status=HttpResponseForbidden)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator



class IsCompanyOwnerOrAdmin(BasePermission):
    """
    Permission for company owners or admin users
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class CanApplyToJob(BasePermission):
    """
    Permission to apply to jobs - user only, not to own company jobs
    """
    def has_object_permission(self, request, view, obj):
        # Only job seekers can apply
        if request.user.role != 'user':
            return False
        
        # Can't apply to jobs from own company (if user is also an employer)
        if hasattr(obj, 'company') and hasattr(obj.company, 'created_by'):
            return obj.company.created_by != request.user
        
        return True


class CanManageJobApplications(BasePermission):
    """
    Permission to manage job applications - company owners and admins
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'job') and hasattr(obj.job, 'company'):
            return obj.job.company.created_by == request.user
        
        return False


class ReadOnlyOrOwnerWrite(BasePermission):
    """
    Permission that allows read-only access to everyone, but write access only to owner
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return obj == request.user


class IsAccountOwnerOrAdmin(BasePermission):
    """
    Permission for account owners or admin users to manage user accounts
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj == request.user
```

Job Board Platform - Project Structure

jobboard/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── README.md
├── manage.py
├── celery_worker.py
├── jobboard/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── pagination.py
│   │   ├── exceptions.py
│   │   └── utils.py
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── managers.py
│   │   ├── tasks.py
│   │   └── signals.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── filters.py
│   │   ├── tasks.py
│   │   ├── search.py
│   │   └── signals.py
│   └── companies/
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py
│       ├── admin.py
│       ├── views.py
│       ├── urls.py
│       ├── serializers.py
│       ├── tasks.py
│       └── signals.py
├── static/
│   ├── css/
│   ├── js/
│   ├── img/
│   └── admin/
├── media/
│   ├── avatars/
│   ├── resumes/
│   ├── company_logos/
│   └── application_resumes/
├── templates/
│   ├── base.html
│   ├── emails/
│   │   ├── base_email.html
│   │   ├── welcome.html
│   │   ├── verification.html
│   │   └── job_alert.html
│   └── admin/
├── logs/
├── locale/
└── scripts/
    ├── start.sh
    ├── migrate.sh
    └── seed_data.py

Models:

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.db.models import Q, Count, Avg
import uuid
import re

# Custom Managers

class ActiveManager(models.Manager):
    """Manager for models with is_active field"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class PublishedJobManager(models.Manager):
    """Manager for published jobs only"""
    def get_queryset(self):
        return super().get_queryset().filter(
            status='published',
            published_at__isnull=False
        )

    def active(self):
        """Returns only active jobs (published and not expired)"""
        return self.get_queryset().filter(
            Q(application_deadline__isnull=True) | Q(application_deadline__gt=timezone.now())
        )

    def featured(self):
        """Returns featured jobs"""
        return self.get_queryset().filter(is_featured=True)

    def by_location(self, location):
        """Filter jobs by location"""
        return self.get_queryset().filter(
            Q(location__icontains=location) | Q(remote_allowed=True)
        )

    def by_salary_range(self, min_salary=None, max_salary=None):
        """Filter jobs by salary range"""
        queryset = self.get_queryset()
        if min_salary:
            queryset = queryset.filter(salary_min__gte=min_salary)
        if max_salary:
            queryset = queryset.filter(salary_max__lte=max_salary)
        return queryset

    def with_company_info(self):
        """Prefetch company and industry data"""
        return self.get_queryset().select_related('company', 'industry', 'category')

class JobApplicationManager(models.Manager):
    """Manager for job applications"""
    def pending(self):
        return self.get_queryset().filter(status='pending')

    def under_review(self):
        return self.get_queryset().filter(status='under_review')
    
    def accepted(self):
        return self.get_queryset().filter(status='accepted')
    
    def rejected(self):
        return self.get_queryset().filter(status='rejected')
    
    def by_user(self, user):
        return self.get_queryset().filter(applicant=user)
    
    def by_company(self, company):
        return self.get_queryset().filter(job__company=company)

# Custom Validators

def validate_phone_number(value):
    """Validate phone number format"""
    phone_regex = re.compile(r'^\+?1?\d{9,15}$')
    if not phone_regex.match(value):
        raise ValidationError('Invalid phone number format')

def validate_linkedin_url(value):
    """Validate LinkedIn URL format"""
    linkedin_regex = re.compile(r'^https?://(www\.)?linkedin\.com/in/[\w-]+/?$')
    if not linkedin_regex.match(value):
        raise ValidationError('Invalid LinkedIn URL format')

def validate_github_url(value):
    """Validate GitHub URL format"""
    github_regex = re.compile(r'^https?://(www\.)?github\.com/[\w-]+/?$')
    if not github_regex.match(value):
        raise ValidationError('Invalid GitHub URL format')

def validate_salary_range(salary_min, salary_max):
    """Validate that salary_min <= salary_max"""
    if salary_min and salary_max and salary_min > salary_max:
        raise ValidationError('Minimum salary cannot be greater than maximum salary')

# Models

class User(AbstractUser):
    """
    Extended user model with role-based access control
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('employer', 'Employer'),
        ('job_seeker', 'Job Seeker'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='job_seeker', db_index=True)
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[validate_phone_number]
    )
    is_verified = models.BooleanField(default=False, db_index=True)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['is_verified', 'created_at']),
            models.Index(fields=['last_login', 'is_active']),
        ]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def get_full_name(self):
        """Return full name or email if names not available"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def is_employer(self):
        """Check if user is an employer"""
        return self.role == 'employer'
    
    def is_job_seeker(self):
        """Check if user is a job seeker"""
        return self.role == 'job_seeker'
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin' or self.is_superuser

class Profile(models.Model):
    """
    Extended profile information for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, help_text="Brief professional summary")
    location = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    website = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(
        blank=True,
        null=True,
        validators=[validate_linkedin_url]
    )
    github_url = models.URLField(
        blank=True,
        null=True,
        validators=[validate_github_url]
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    skills = models.ManyToManyField('Skill', blank=True, related_name='profiles')
    experience_years = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(50)]
    )
    salary_expectation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
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
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
    
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

class Industry(models.Model):
    """
    Industry categories for companies and jobs
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class or emoji")
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        db_table = 'industries'
        verbose_name_plural = 'Industries'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_job_count(self):
        """Return count of active jobs in this industry"""
        return self.jobs.filter(status='published').count()

class JobCategory(models.Model):
    """
    Job categories for organizing job postings
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        db_table = 'job_categories'
        verbose_name_plural = 'Job Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_job_count(self, include_subcategories=False):
        """Return count of jobs in this category"""
        if include_subcategories:
            categories = [self] + list(self.subcategories.all())
            return Job.published.filter(category__in=categories).count()
        return self.jobs.filter(status='published').count()

class SkillCategory(models.Model):
    """
    Categories for organizing skills
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        db_table = 'skill_categories'
        verbose_name_plural = 'Skill Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Skill(models.Model):
    """
    Skills that can be associated with jobs and profiles
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, db_index=True)
    category = models.ForeignKey(
        SkillCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skills'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    popularity_score = models.PositiveIntegerField(default=0, help_text="Calculated popularity")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        db_table = 'skills'
        ordering = ['-popularity_score', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['popularity_score', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def update_popularity_score(self):
        """Update popularity based on job and profile usage"""
        job_count = self.jobs.filter(status='published').count()
        profile_count = self.profiles.count()
        self.popularity_score = job_count + profile_count
        self.save(update_fields=['popularity_score'])

class Company(models.Model):
    """
    Company model for employers
    """
    COMPANY_SIZES = [
        ('startup', '1-10 employees'),
        ('small', '11-50 employees'),
        ('medium', '51-200 employees'),
        ('large', '201-1000 employees'),
        ('enterprise', '1000+ employees'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    founded_year = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[
            MinValueValidator(1800),
            MaxValueValidator(timezone.now().year)
        ]
    )
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZES, blank=True, null=True)
    industry = models.ForeignKey(
        Industry, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='companies'
    )
    location = models.CharField(max_length=200, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    is_verified = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False)
    employee_count = models.PositiveIntegerField(blank=True, null=True)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['name', 'is_verified']),
            models.Index(fields=['location', 'is_verified']),
            models.Index(fields=['industry', 'is_verified']),
            models.Index(fields=['is_featured', 'created_at']),
            models.Index(fields=['company_size', 'is_verified']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('company_detail', kwargs={'slug': self.slug})
    
    def get_job_count(self):
        """Return count of active jobs"""
        return self.jobs.filter(status='published').count()
    
    def get_average_salary(self):
        """Calculate average salary for company jobs"""
        jobs = self.jobs.filter(
            status='published',
            salary_min__isnull=False,
            salary_max__isnull=False
        )
        if jobs.exists():
            return jobs.aggregate(
                avg_min=Avg('salary_min'),
                avg_max=Avg('salary_max')
            )
        return None

class JobType(models.Model):
    """
    Job types for filtering and alerts
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        db_table = 'job_types'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Job(models.Model):
    """
    Main job posting model
    """
    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]

    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead/Principal'),
        ('executive', 'Executive'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('on_hold', 'On Hold'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('NGN', 'Nigerian Naira'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField()
    benefits = models.TextField(blank=True)
    
    # Relationships
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(
        JobCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='jobs'
    )
    industry = models.ForeignKey(
        Industry, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='jobs'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs')
    skills = models.ManyToManyField(Skill, blank=True, related_name='jobs')
    
    # Job details
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, db_index=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, db_index=True)
    location = models.CharField(max_length=200, db_index=True)
    remote_allowed = models.BooleanField(default=False, db_index=True)
    salary_min = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    salary_max = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    salary_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    salary_negotiable = models.BooleanField(default=False)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_urgent = models.BooleanField(default=False)
    application_deadline = models.DateTimeField(blank=True, null=True, db_index=True)
    start_date = models.DateField(blank=True, null=True)
    
    # Metadata
    views_count = models.PositiveIntegerField(default=0, db_index=True)
    applications_count = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    
    # Managers
    objects = models.Manager()
    published = PublishedJobManager()
    
    class Meta:
        db_table = 'jobs'
        ordering = ['-is_featured', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['location', 'remote_allowed']),
            models.Index(fields=['job_type', 'status']),
            models.Index(fields=['experience_level', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['application_deadline']),
            models.Index(fields=['salary_min', 'salary_max']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['industry', 'status']),
            models.Index(fields=['views_count']),
            models.Index(fields=['applications_count']),
        ]
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
    def clean(self):
        """Custom validation"""
        validate_salary_range(self.salary_min, self.salary_max)
        
        if self.application_deadline and self.application_deadline <= timezone.now():
            raise ValidationError('Application deadline must be in the future')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.title}-{self.company.name}")
            self.slug = base_slug
            counter = 1
            while Job.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('job_detail', kwargs={'slug': self.slug})
    
    @property
    def is_active(self):
        """Check if job is active and accepting applications"""
        return (
            self.status == 'published' and
            (self.application_deadline is None or self.application_deadline > timezone.now())
        )
    
    @property
    def days_since_posted(self):
        """Calculate days since job was posted"""
        if self.published_at:
            return (timezone.now() - self.published_at).days
        return None
    
    @property
    def salary_range_display(self):
        """Return formatted salary range"""
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,.0f} - {self.salary_max:,.0f}"
        elif self.salary_min:
            return f"{self.salary_currency} {self.salary_min:,.0f}+"
        elif self.salary_max:
            return f"Up to {self.salary_currency} {self.salary_max:,.0f}"
        return "Competitive"
    
    def increment_views(self):
        """Increment view count"""
        Job.objects.filter(pk=self.pk).update(views_count=models.F('views_count') + 1)
    
    def increment_applications(self):
        """Increment applications count"""
        Job.objects.filter(pk=self.pk).update(applications_count=models.F('applications_count') + 1)
    
    def get_similar_jobs(self, limit=5):
        """Get similar jobs based on category, skills, and location"""
        similar_jobs = Job.published.active().exclude(pk=self.pk)
        
        if self.category:
            similar_jobs = similar_jobs.filter(category=self.category)
        
        if self.skills.exists():
            similar_jobs = similar_jobs.filter(skills__in=self.skills.all()).distinct()
        
        return similar_jobs.order_by('-published_at')[:limit]

class JobApplication(models.Model):
    """
    Job applications submitted by users
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interview_completed', 'Interview Completed'),
        ('offer_made', 'Offer Made'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='application_resumes/', blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', db_index=True)
    notes = models.TextField(blank=True, help_text="Internal notes from recruiters")
    score = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Internal scoring (1-10)"
    )
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, db_index=True)
    
    objects = JobApplicationManager()
    
    class Meta:
        db_table = 'job_applications'
        unique_together = ['job', 'applicant']  # One application per job per user
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['status', 'applied_at']),
            models.Index(fields=['job', 'status']),
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['reviewed_at']),
            models.Index(fields=['score']),
        ]
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
    
    def __str__(self):
        return f"{self.applicant.get_full_name()} applied for {self.job.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Increment job applications count for new applications
        if is_new:
            self.job.increment_applications()
    
    @property
    def days_since_applied(self):
        """Calculate days since application was submitted"""
        return (timezone.now() - self.applied_at).days
    
    def can_withdraw(self):
        """Check if application can be withdrawn"""
        return self.status in ['pending', 'under_review']
    
    def withdraw(self, user=None):
        """Withdraw the application"""
        if self.can_withdraw():
            self.status = 'withdrawn'
            self.reviewed_by = user
            self.reviewed_at = timezone.now()
            self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
            return True
        return False

class SavedJob(models.Model):
    """
    Jobs saved by users for later application
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField(blank=True, help_text="Personal notes about this job")

    class Meta:
        db_table = 'saved_jobs'
        unique_together = ['user', 'job']
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['user', 'saved_at']),
            models.Index(fields=['job', 'saved_at']),
        ]
        verbose_name = 'Saved Job'
        verbose_name_plural = 'Saved Jobs'
    
    def __str__(self):
        return f"{self.user.get_full_name()} saved {self.job.title}"

class JobView(models.Model):
    """
    Track job views for analytics
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)
    duration = models.PositiveIntegerField(blank=True, null=True, help_text="View duration in seconds")

    class Meta:
        db_table = 'job_views'
        indexes = [
            models.Index(fields=['job', 'viewed_at']),
            models.Index(fields=['ip_address', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['session_key', 'viewed_at']),
        ]
        verbose_name = 'Job View'
        verbose_name_plural = 'Job Views'
    
    def __str__(self):
        return f"View of {self.job.title} at {self.viewed_at}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Increment job views count for new views
        if is_new:
            self.job.increment_views()

class JobAlert(models.Model):
    """
    Job alerts/notifications for users
    """
    FREQUENCY_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_alerts')
    name = models.CharField(max_length=200, help_text="Name for this alert")
    keywords = models.CharField(max_length=500, blank=True, help_text="Comma-separated keywords")
    location = models.CharField(max_length=200, blank=True)
    remote_only = models.BooleanField(default=False)
    job_types = models.ManyToManyField(JobType, blank=True)
    categories = models.ManyToManyField(JobCategory, blank=True)
    industries = models.ManyToManyField(Industry, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    experience_levels = models.JSONField(default=list, blank=True)
    salary_min = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    salary_currency = models.CharField(max_length=3, default='USD')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    is_active = models.BooleanField(default=True, db_index=True)
    last_sent = models.DateTimeField(blank=True, null=True, db_index=True)
    jobs_sent_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_alerts'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['frequency', 'is_active']),
            models.Index(fields=['last_sent', 'is_active']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Job Alert'
        verbose_name_plural = 'Job Alerts'
    
    def __str__(self):
        return f"{self.name} - {self.user.get_full_name()}"
    
    def get_matching_jobs(self):
        """Get jobs that match this alert criteria"""
        jobs = Job.published.active()
        
        # Filter by keywords
        if self.keywords:
            keywords = [kw.strip().lower() for kw in self.keywords.split(',') if kw.strip()]
            q_objects = Q()
            for keyword in keywords:
                q_objects |= (
                    Q(title__icontains=keyword) |
                    Q(description__icontains=keyword) |
                    Q(requirements__icontains=keyword)
                )
            jobs = jobs.filter(q_objects)
        
        # Filter by location
        if self.location and not self.remote_only:
            jobs = jobs.filter(location__icontains=self.location)
        elif self.remote_only:
            jobs = jobs.filter(remote_allowed=True)
        
        # Filter by job types
        if self.job_types.exists():
            job_type_names = [jt.slug for jt in self.job_types.all()]
            jobs = jobs.filter(job_type__in=job_type_names)
        
        # Filter by categories
        if self.categories.exists():
            jobs = jobs.filter(category__in=self.categories.all())
        
        # Filter by industries
        if self.industries.exists():
            jobs = jobs.filter(industry__in=self.industries.all())
        
        # Filter by skills
        if self.skills.exists():
            jobs = jobs.filter(skills__in=self.skills.all()).distinct()
        
        # Filter by experience levels
        if self.experience_levels:
            jobs = jobs.filter(experience_level__in=self.experience_levels)
        
        # Filter by salary
        if self.salary_min:
            jobs = jobs.filter(salary_min__gte=self.salary_min)
        
        return jobs.distinct()
    
    def should_send_alert(self):
        """Check if alert should be sent based on frequency"""
        if not self.is_active:
            return False
        
        if not self.last_sent:
            return True
        
        now = timezone.now()
        time_diff = now - self.last_sent
        
        frequency_map = {
            'immediate': timezone.timedelta(minutes=5),
            'daily': timezone.timedelta(days=1),
            'weekly': timezone.timedelta(weeks=1),
            'monthly': timezone.timedelta(days=30),
        }
        
        return time_diff >= frequency_map.get(self.frequency, timezone.timedelta(days=7))
    
    def mark_as_sent(self, job_count=0):
        """Mark alert as sent"""
        self.last_sent = timezone.now()
        self.jobs_sent_count += job_count
        self.save(update_fields=['last_sent', 'jobs_sent_count'])

# Audit trail model

class AuditLog(models.Model):
    """
    Audit log for tracking important actions
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('apply', 'Apply'),
        ('view', 'View'),
        ('save_job', 'Save Job'),
        ('unsave_job', 'Unsave Job'),
        ('withdraw_application', 'Withdraw Application'),
        ('change_status', 'Change Status'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    object_type = models.CharField(max_length=50, db_index=True)
    object_id = models.CharField(max_length=100, db_index=True)
    object_repr = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['session_key', 'timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.get_action_display()} {self.object_type} by {self.user or 'Anonymous'}"
    
    @classmethod
    def log_action(cls, user, action, obj, details=None, request=None):
        """Helper method to create audit log entries"""
        log_data = {
            'user': user,
            'action': action,
            'object_type': obj.__class__.__name__,
            'object_id': str(obj.pk),
            'object_repr': str(obj),
            'details': details or {},
        }
        
        if request:
            log_data.update({
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'session_key': request.session.session_key,
            })
        
        return cls.objects.create(**log_data)

# Signal handlers for automatic logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation and updates"""
    action = 'create' if created else 'update'
    AuditLog.log_action(
        user=instance,
        action=action,
        obj=instance,
        details={'role': instance.role, 'is_verified': instance.is_verified}
    )

@receiver(post_save, sender=Job)
def log_job_changes(sender, instance, created, **kwargs):
    """Log job creation and updates"""
    action = 'create' if created else 'update'
    AuditLog.log_action(
        user=instance.created_by,
        action=action,
        obj=instance,
        details={
            'status': instance.status,
            'company': instance.company.name,
            'job_type': instance.job_type
        }
    )

@receiver(post_save, sender=JobApplication)
def log_application_changes(sender, instance, created, **kwargs):
    """Log job application creation and status changes"""
    action = 'apply' if created else 'change_status'
    AuditLog.log_action(
        user=instance.applicant,
        action=action,
        obj=instance,
        details={
            'job_title': instance.job.title,
            'company': instance.job.company.name,
            'status': instance.status
        }
    )

@receiver(post_save, sender=SavedJob)
def log_saved_job(sender, instance, created, **kwargs):
    """Log when users save jobs"""
    if created:
        AuditLog.log_action(
            user=instance.user,
            action='save_job',
            obj=instance,
            details={
                'job_title': instance.job.title,
                'company': instance.job.company.name
            }
        )

@receiver(post_delete, sender=SavedJob)
def log_unsaved_job(sender, instance, **kwargs):
    """Log when users unsave jobs"""
    AuditLog.log_action(
        user=instance.user,
        action='unsave_job',
        obj=instance,
        details={
            'job_title': instance.job.title,
            'company': instance.job.company.name
        }
    )

# Custom model methods and properties

def get_user_display_name(self):
    """Get display name for user"""
    if self.first_name and self.last_name:
        return f"{self.first_name} {self.last_name}"
    elif self.first_name:
        return self.first_name
    return self.username or self.email

# Add the method to User model

User.add_to_class('get_display_name', get_user_display_name)
