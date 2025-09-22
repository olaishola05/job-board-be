from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.core.models import AuditLog
from .models import Job, JobApplication, SavedJob


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
