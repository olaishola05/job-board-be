from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
import uuid
from apps.core.managers import ActiveManager
from django.contrib.auth import get_user_model


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