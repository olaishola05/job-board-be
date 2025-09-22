from django.db import models
from django.db.models import Count


class CompanyManager(models.Manager):
    def verified(self):
        return self.get_queryset().filter(is_verified=True)
    
    def featured(self):
        return self.get_queryset().filter(is_featured=True)
    
    def by_industry(self, industry):
        return self.get_queryset().filter(industry=industry)
    
    def with_jobs(self):
        return self.get_queryset().annotate(job_count=Count('jobs')).filter(job_count__gt=0)