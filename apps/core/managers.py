from django.db import models

class ActiveManager(models.Manager):
    """Manager for models with is_active field"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)