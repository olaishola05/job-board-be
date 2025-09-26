from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from apps.core.models import AuditLog
from .models import Job, JobApplication, SavedJob
from .tasks import send_job_published_notification, send_application_received_notification
from django.utils import timezone



@receiver(post_save, sender=Job)
def job_post_save_handler(sender, instance, created, **kwargs):
    '''Trigger tasks when job is saved'''
    if not created:
        # Check if job was just published
        if instance.status == 'published' and instance.published_at:
            # Check if published_at was just set (within last minute)
            if (timezone.now() - instance.published_at).seconds < 60:
                send_job_published_notification.delay(instance.id) # type: ignore

@receiver(post_save, sender=JobApplication)
def application_post_save_handler(sender, instance, created, **kwargs):
    '''Trigger tasks when application is saved'''
    if created:
        send_application_received_notification.delay(instance.id) # type: ignore


@receiver(pre_save, sender=JobApplication)
def application_pre_save_handler(sender, instance, **kwargs):
    """Track status changes for applications"""
    if instance.pk:
        try:
            old_instance = JobApplication.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                instance._status_changed = (old_instance.status, instance.status)
        except JobApplication.DoesNotExist:
            pass
          
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
