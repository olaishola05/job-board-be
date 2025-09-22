import django_filters
from django.db.models import Q
from .models import Company

class CompanyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    industry = django_filters.UUIDFilter(field_name='industry__id')
    company_size = django_filters.ChoiceFilter(choices=Company.COMPANY_SIZES)
    is_verified = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    founded_year_min = django_filters.NumberFilter(field_name='founded_year', lookup_expr='gte')
    founded_year_max = django_filters.NumberFilter(field_name='founded_year', lookup_expr='lte')
    has_jobs = django_filters.BooleanFilter(method='filter_has_jobs')
    approval_status = django_filters.ChoiceFilter(choices=Company.APPROVAL_STATUS)
    
    class Meta:
        model = Company
        fields = [
            'name', 'location', 'industry', 'company_size', 'is_verified',
            'is_featured', 'min_rating', 'max_rating', 'founded_year_min',
            'founded_year_max', 'has_jobs', 'approval_status'
        ]
    
    def filter_has_jobs(self, queryset, name, value):
        if value:
            return queryset.filter(jobs__status='published').distinct()
        return queryset