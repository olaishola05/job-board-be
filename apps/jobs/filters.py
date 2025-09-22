import django_filters
from django.db.models import Q
from .models import Job, JobCategory, Industry, Company, Skill, JobApplication

class JobFilter(django_filters.FilterSet):
    # Text search
    q = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Location filters
    location = django_filters.CharFilter(lookup_expr='icontains')
    remote_only = django_filters.BooleanFilter(field_name='remote_allowed')
    
    # Job type and experience
    job_type = django_filters.MultipleChoiceFilter(
        choices=Job.JOB_TYPES,
        lookup_expr='in'
    )
    experience_level = django_filters.MultipleChoiceFilter(
        choices=Job.EXPERIENCE_LEVELS,
        lookup_expr='in'
    )
    
    # Category and industry
    category = django_filters.ModelMultipleChoiceFilter(
        queryset=JobCategory.active.all(),
        field_name='category'
    )
    industry = django_filters.ModelMultipleChoiceFilter(
        queryset=Industry.active.all(),
        field_name='industry'
    )
    
    # Company
    company = django_filters.ModelMultipleChoiceFilter(
        queryset=Company.objects.filter(is_verified=True),
        field_name='company'
    )
    
    # Salary filters
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    salary_range = django_filters.RangeFilter(field_name='salary_min')
    has_salary = django_filters.BooleanFilter(method='filter_has_salary')
    
    # Skills
    skills = django_filters.ModelMultipleChoiceFilter(
        queryset=Skill.active.all(),
        field_name='skills'
    )
    
    # Status filters
    status = django_filters.MultipleChoiceFilter(
        choices=Job.STATUS_CHOICES,
        lookup_expr='in'
    )
    is_featured = django_filters.BooleanFilter()
    is_urgent = django_filters.BooleanFilter()
    
    # Date filters
    posted_days_ago = django_filters.NumberFilter(method='filter_posted_days_ago')
    published_after = django_filters.DateTimeFilter(
        field_name='published_at', 
        lookup_expr='gte'
    )
    published_before = django_filters.DateTimeFilter(
        field_name='published_at', 
        lookup_expr='lte'
    )
    
    # Application deadline
    deadline_after = django_filters.DateTimeFilter(
        field_name='application_deadline',
        lookup_expr='gte'
    )
    deadline_before = django_filters.DateTimeFilter(
        field_name='application_deadline',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Job
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(requirements__icontains=value) |
                Q(responsibilities__icontains=value) |
                Q(company__name__icontains=value) |
                Q(skills__name__icontains=value)
            ).distinct()
        return queryset
    
    def filter_has_salary(self, queryset, name, value):
        """Filter jobs that have salary information"""
        if value:
            return queryset.filter(
                Q(salary_min__isnull=False) | Q(salary_max__isnull=False)
            )
        else:
            return queryset.filter(
                salary_min__isnull=True, salary_max__isnull=True
            )
    
    def filter_posted_days_ago(self, queryset, name, value):
        """Filter jobs posted within X days"""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            cutoff_date = timezone.now() - timedelta(days=int(value))
            return queryset.filter(published_at__gte=cutoff_date)
        return queryset

class JobApplicationFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=JobApplication.STATUS_CHOICES,
        lookup_expr='in'
    )
    job_title = django_filters.CharFilter(
        field_name='job__title',
        lookup_expr='icontains'
    )
    company = django_filters.CharFilter(
        field_name='job__company__name',
        lookup_expr='icontains'
    )
    applied_after = django_filters.DateTimeFilter(
        field_name='applied_at',
        lookup_expr='gte'
    )
    applied_before = django_filters.DateTimeFilter(
        field_name='applied_at',
        lookup_expr='lte'
    )
    score_min = django_filters.NumberFilter(
        field_name='score',
        lookup_expr='gte'
    )
    score_max = django_filters.NumberFilter(
        field_name='score',
        lookup_expr='lte'
    )
    reviewed = django_filters.BooleanFilter(method='filter_reviewed')
    
    class Meta:
        model = JobApplication
        fields = []
    
    def filter_reviewed(self, queryset, name, value):
        """Filter reviewed/unreviewed applications"""
        if value:
            return queryset.filter(reviewed_at__isnull=False)
        else:
            return queryset.filter(reviewed_at__isnull=True)