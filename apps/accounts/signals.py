from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_login_failed
from .models import User, Profile
from apps.core.models import AuditLog
from ipware import get_client_ip
from apps.core.utils import send_email
from logging import getLogger
from .utils import log_login_attempt

logger = getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create profile when user is created
    """
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save profile when user is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
        logger.info(f"Profile saved for user: {instance.email}")

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation and updates"""
    action = 'create' if created else 'update'
    AuditLog.log_action(
        user=instance,
        action=action,
        obj=instance,
        details={'role': instance.role, 'is_verified': instance.is_verified}
    )
    logger.info(f"User {action}d: {instance.email}")


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Handle successful login
    """
    client_ip, _ = get_client_ip(request)
    if client_ip:
        user.last_login_ip = client_ip
        user.save(update_fields=['last_login_ip'])
    
    user.reset_failed_attempts()
    logger.info(f"User logged in: {user.email} from IP: {client_ip}")


@receiver(user_login_failed)
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """
    Handle failed login attempts
    """
    email = credentials.get('username')
    
    if email:
        log_login_attempt(
            email=email,
            success=False,
            failure_reason='Invalid credentials',
            request=request
        )
        
        try:
            user = User.objects.get(email__iexact=email)
            old_attempts = user.failed_login_attempts
            user.increment_failed_attempts()
            
            if old_attempts < 5 and user.failed_login_attempts >= 5:
                send_email(
                    subject="Alert: Multiple Failed Login Attempts",
                    to_email=[user.email],
                    template='emails/account_locked.html',
                    context={'user': user, 'attempts': user.failed_login_attempts}
                )
                user.lock_account()
                logger.warning(f"Account locked due to too many failed login attempts: {user.email}")
                
        except User.DoesNotExist:
            logger.warning(f"Failed login attempt for non-existent user: {email}")