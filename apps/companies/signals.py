from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Company, Industry, CompanyFollow, CompanyReview, CompanyAnalytics
from apps.core.models import AuditLog
from django.dispatch import Signal
from django.db.models import F
from django.core.cache import cache
from .tasks import update_company_ratings
from logging import getLogger

User = get_user_model()
logger = getLogger(__name__)


@receiver(post_save, sender=Company)
def log_company_changes(sender, instance, created, **kwargs):
    """Log company creation and updates"""
    action = 'create' if created else 'update'

    user = instance.created_by if created else getattr(instance, '_updated_by', instance.created_by)
    
    details = {
        'name': instance.name,
        'location': instance.location,
        'is_verified': instance.is_verified,
        'is_featured': instance.is_featured,
        'industry': instance.industry.name if instance.industry else None,
        'company_size': instance.company_size,
    }
    
    # Add specific details for updates
    if not created:
        if hasattr(instance, '_changed_fields'):
            details['changed_fields'] = instance._changed_fields
    
    AuditLog.log_action(
        user=user,
        action=action,
        obj=instance,
        details=details
    )
    logger.info(f"Company {action}d: {instance.name}")


@receiver(post_delete, sender=Company)
def log_company_deletion(sender, instance, **kwargs):
    """Log company deletion"""
    AuditLog.log_action(
        user=getattr(instance, '_deleted_by', None),
        action='delete',
        obj=instance,
        details={
            'name': instance.name,
            'location': instance.location,
            'job_count': instance.jobs.count(),
        }
    )
    logger.info(f"Company deleted: {instance.name} by")


@receiver(pre_save, sender=Company)
def track_company_changes(sender, instance, **kwargs):
    """Track what fields changed before saving"""
    if instance.pk:
        try:
            old_instance = Company.objects.get(pk=instance.pk)
            changed_fields = {}
            
            fields_to_check = [
                'name', 'description', 'location', 'website', 
                'is_verified', 'is_featured', 'company_size', 
                'industry_id', 'employee_count'
            ]
            
            for field in fields_to_check:
                old_value = getattr(old_instance, field, None)
                new_value = getattr(instance, field, None)
                
                if old_value != new_value:
                    changed_fields[field] = {
                        'old': old_value,
                        'new': new_value
                    }
            
            instance._changed_fields = changed_fields
            
            # Special logging for verification status changes
            if old_instance.is_verified != instance.is_verified:
                action = 'verify' if instance.is_verified else 'unverify'
                AuditLog.log_action(
                    user=getattr(instance, '_updated_by', instance.created_by),
                    action=action,
                    obj=instance,
                    details={
                        'previous_status': old_instance.is_verified,
                        'new_status': instance.is_verified,
                        'name': instance.name
                    }
                )
            
            # Special logging for featured status changes
            if old_instance.is_featured != instance.is_featured:
                action = 'feature' if instance.is_featured else 'unfeature'
                AuditLog.log_action(
                    user=getattr(instance, '_updated_by', instance.created_by),
                    action=action,
                    obj=instance,
                    details={
                        'previous_status': old_instance.is_featured,
                        'new_status': instance.is_featured,
                        'name': instance.name
                    }
                )
                logger.info(f"Company {action}d: {instance.name}")
                
        except Company.DoesNotExist:
          logger.warning(f"Old instance for Company with id {instance.pk} does not exist.")

@receiver(post_save, sender=Industry)
def log_industry_changes(sender, instance, created, **kwargs):
    """Log industry creation and updates"""
    action = 'create' if created else 'update'
    
    details = {
        'name': instance.name,
        'slug': instance.slug,
        'is_active': instance.is_active,
    }
    user = getattr(instance, '_updated_by', None)
    
    AuditLog.log_action(
        user=user,
        action=action,
        obj=instance,
        details=details
    )
    logger.info(f"Industry {action}d: {instance.name}")


@receiver(post_delete, sender=Industry)
def log_industry_deletion(sender, instance, **kwargs):
    """Log industry deletion"""
    AuditLog.log_action(
        user=getattr(instance, '_deleted_by', None),
        action='delete',
        obj=instance,
        details={
            'name': instance.name,
            'slug': instance.slug,
            'company_count': instance.companies.count() if hasattr(instance, 'companies') else 0,
        }
    )
    logger.info(f"Industry deleted: {instance.name} by {getattr(instance, '_deleted_by', None)}")

@receiver(post_save, sender=Company)
def create_company_analytics(sender, instance, created, **kwargs):
    """Create analytics record for new company"""
    if created:
        CompanyAnalytics.objects.get_or_create(company=instance)
        logger.info(f"Analytics created for new company: {instance.name}")

@receiver(post_save, sender=Company)
def clear_company_cache(sender, instance, **kwargs):
    """Clear company-related cache on update"""
    cache_keys = [
        'company_stats',
        f'company_detail_{instance.slug}',
        f'company_jobs_{instance.id}',
    ]
    cache.delete_many(cache_keys)

@receiver(post_save, sender=CompanyFollow)
def update_follower_count_on_follow(sender, instance, created, **kwargs):
    """Update company follower count when followed"""
    if created:
        Company.objects.filter(pk=instance.company.pk).update(
            follower_count=F('follower_count') + 1
        )

@receiver(post_delete, sender=CompanyFollow)
def update_follower_count_on_unfollow(sender, instance, **kwargs):
    """Update company follower count when unfollowed"""
    Company.objects.filter(pk=instance.company.pk).update(
        follower_count=F('follower_count') - 1
    )

@receiver(post_save, sender=CompanyReview)
def update_company_rating_on_review(sender, instance, created, **kwargs):
    """Update company rating when review is added/updated"""
    if created or not created:
        update_company_ratings.delay()

@receiver(post_delete, sender=CompanyReview)
def update_company_rating_on_review_delete(sender, instance, **kwargs):
    """Update company rating when review is deleted"""
    update_company_ratings.delay()

@receiver(pre_save, sender=Company)
def handle_company_approval(sender, instance, **kwargs):
    """Handle company approval workflow"""
    if instance.pk:
        try:
            old_instance = Company.objects.get(pk=instance.pk)
            if (old_instance.approval_status != instance.approval_status and 
                instance.approval_status == 'approved'):
                from apps.core.utils import send_email
                send_email(
                    to_email=instance.created_by.email,
                    template='emails/company_approved.html',
                    context={'company': instance, 'user': instance.created_by},
                    subject=f'Your company {instance.name} has been approved!'
                )
        except Company.DoesNotExist:
            logger.warning(f"Old instance for Company with id {instance.pk} does not exist.")

company_verified = Signal()
company_featured = Signal()


@receiver(company_verified)
def handle_company_verification(sender, company, verified_by, **kwargs):
    """Handle company verification event"""
    AuditLog.log_action(
        user=verified_by,
        action='verify_company',
        obj=company,
        details={
            'company_name': company.name,
            'verified_by': verified_by.get_full_name() if verified_by else 'System',
            'verification_date': company.updated_at.isoformat(),
        }
    )


@receiver(company_featured)
def handle_company_featured(sender, company, featured_by, **kwargs):
    """Handle company featured event"""
    AuditLog.log_action(
        user=featured_by,
        action='feature_company',
        obj=company,
        details={
            'company_name': company.name,
            'featured_by': featured_by.get_full_name() if featured_by else 'System',
            'featured_date': company.updated_at.isoformat(),
        }
    )
