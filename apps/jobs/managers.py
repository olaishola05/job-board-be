from django.db import models
from django.utils import timezone
from django.db.models import Q

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