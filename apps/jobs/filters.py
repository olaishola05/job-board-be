import django_filters
from django.db.models import Q
from .models import Job, JobApplication
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
    # 
    class Meta:
        model = JobApplication
        fields = []
    # 
    def filter_reviewed(self, queryset, name, value):
        """Filter reviewed/unreviewed applications"""
        if value:
            return queryset.filter(reviewed_at__isnull=False)
        else:
            return queryset.filter(reviewed_at__isnull=True)

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
    
    # Enhanced filters that accept both IDs and names
    category = django_filters.CharFilter(method='filter_category')
    industry = django_filters.CharFilter(method='filter_industry') 
    company = django_filters.CharFilter(method='filter_company')
    skills = django_filters.CharFilter(method='filter_skills')
    
    # Salary filters
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    salary_range = django_filters.RangeFilter(field_name='salary_min')
    has_salary = django_filters.BooleanFilter(method='filter_has_salary')
    
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
    
    def _is_uuid(self, value):
        """Check if value is a valid UUID"""
        try:
            import uuid
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_numeric(self, value):
        """Check if value is numeric (for integer IDs)"""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def filter_search(self, queryset, name, value):
        """Enhanced full-text search across multiple fields"""
        if value:
            search_terms = value.split()
            search_query = Q()
            
            for term in search_terms:
                term_query = (
                    Q(title__icontains=term) |
                    Q(description__icontains=term) |
                    Q(requirements__icontains=term) |
                    Q(responsibilities__icontains=term) |
                    Q(company__name__icontains=term) |
                    Q(skills__name__icontains=term) |
                    Q(category__name__icontains=term) |
                    Q(industry__name__icontains=term)
                )
                search_query &= term_query
            
            return queryset.filter(search_query).distinct()
        return queryset
    
    def filter_category(self, queryset, name, value):
        """Filter by category - accepts both ID/UUID and name"""
        if not value:
            return queryset
            
        # Handle comma-separated values
        values = [v.strip() for v in value.split(',')]
        category_query = Q()
        
        for val in values:
            if self._is_uuid(val) or self._is_numeric(val):
                # Filter by ID
                category_query |= Q(category__id=val)
            else:
                # Filter by name
                val.lower()
                category_query |= Q(category__name__icontains=val)
        
        return queryset.filter(category_query).distinct()
    
    def filter_industry(self, queryset, name, value):
        """Filter by industry - accepts both ID/UUID and name"""
        if not value:
            return queryset
            
        values = [v.strip() for v in value.split(',')]
        industry_query = Q()
        
        for val in values:
            if self._is_uuid(val) or self._is_numeric(val):
                # Filter by ID
                industry_query |= Q(industry__id=val)
            else:
                # Filter by name
                industry_query |= Q(industry__name__icontains=val)
        
        return queryset.filter(industry_query).distinct()
    
    def filter_company(self, queryset, name, value):
        """Filter by company - accepts both ID/UUID and name"""
        if not value:
            return queryset
            
        values = [v.strip() for v in value.split(',')]
        company_query = Q()
        
        for val in values:
            if self._is_uuid(val) or self._is_numeric(val):
                # Filter by ID
                company_query |= Q(company__id=val)
            else:
                # Filter by name
                company_query |= Q(company__name__icontains=val)
        
        return queryset.filter(company_query).distinct()
    
    def filter_skills(self, queryset, name, value):
        """Filter by skills - accepts both ID/UUID and name"""
        if not value:
            return queryset
            
        values = [v.strip() for v in value.split(',')]
        skills_query = Q()
        
        for val in values:
            if self._is_uuid(val) or self._is_numeric(val):
                # Filter by ID
                skills_query |= Q(skills__id=val)
            else:
                # Filter by name
                skills_query |= Q(skills__name__icontains=val)
        
        return queryset.filter(skills_query).distinct()
    
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