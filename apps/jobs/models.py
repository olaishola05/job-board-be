from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.managers import ActiveManager
from apps.jobs.managers import PublishedJobManager
from uuid import uuid4
from django.urls import reverse
from django.db.models import Q
from apps.companies.models import Company, Industry
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .managers import JobApplicationManager
from apps.core.utils import validate_salary_range


User = get_user_model()

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
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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
        unique_together = ['job', 'applicant']
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

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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

