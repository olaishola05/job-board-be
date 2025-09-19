from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
import uuid
from apps.core.managers import ActiveManager
from django.contrib.auth import get_user_model
from decimal import Decimal
from .managers import CompanyManager


User = get_user_model()

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
 
 
class Company(models.Model):
    COMPANY_SIZES = [
        ('startup', '1-10'),
        ('small', '11-50'),
        ('medium', '51-200'),
        ('large', '201-1000'),
        ('enterprise', '1000+'),
    ]
    
    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='company_banners/', blank=True, null=True)
    
    # Company details
    founded_year = models.PositiveIntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1800), MaxValueValidator(timezone.now().year)]
    )
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZES, blank=True, default='')
    employee_count = models.PositiveIntegerField(blank=True, null=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    
    location = models.CharField(max_length=200, db_index=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    is_verified = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    rating = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('5.0'))]
    )
    review_count = models.PositiveIntegerField(default=0)
    follower_count = models.PositiveIntegerField(default=0)
    job_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    linkedin_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    
    objects = CompanyManager()
    active = ActiveManager()
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['name', 'is_verified']),
            models.Index(fields=['location', 'is_active']),
            models.Index(fields=['industry', 'is_verified']),
            models.Index(fields=['approval_status', 'created_at']),
            models.Index(fields=['company_size', 'is_verified']),
            models.Index(fields=['rating', 'review_count']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Company.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('companies:detail', kwargs={'slug': self.slug})
    
    @property
    def average_salary(self):
        from apps.jobs.models import Job
        jobs = Job.objects.filter(
            company=self, status='published',
            salary_min__isnull=False, salary_max__isnull=False
        )
        if jobs.exists():
            return jobs.aggregate(
                avg_min=Avg('salary_min'), avg_max=Avg('salary_max')
            )
        return None

class CompanyFollow(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_companies')
    followed_at = models.DateTimeField(auto_now_add=True)
    notifications_enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['company', 'user']
        indexes = [
            models.Index(fields=['company', 'followed_at']),
            models.Index(fields=['user', 'followed_at']),
        ]

class CompanyReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_reviews')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    pros = models.TextField(blank=True)
    cons = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_current_employee = models.BooleanField(default=False)
    job_title = models.CharField(max_length=100, blank=True)
    employment_status = models.CharField(max_length=20, choices=[
        ('current', 'Current Employee'),
        ('former', 'Former Employee'),
        ('intern', 'Intern'),
        ('contractor', 'Contractor'),
    ], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['company', 'user']
        ordering = ['-created_at']

class CompanyAnalytics(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='analytics')
    total_views = models.PositiveIntegerField(default=0)
    monthly_views = models.PositiveIntegerField(default=0)
    total_job_views = models.PositiveIntegerField(default=0)
    total_applications = models.PositiveIntegerField(default=0)
    avg_time_on_page = models.PositiveIntegerField(default=0)  # seconds
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    top_referrers = models.JSONField(default=dict)
    monthly_stats = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)

class CompanyMedia(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='media')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='company_media/')
    thumbnail = models.ImageField(upload_to='company_media/thumbnails/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']