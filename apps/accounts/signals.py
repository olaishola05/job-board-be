from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_login_failed
from .models import User, Profile, LoginAttempt
from apps.core.models import AuditLog


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


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Handle successful login
    """
    # Update last login IP
    if hasattr(request, 'META'):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])
    
    # Reset failed login attempts
    user.reset_failed_attempts()


@receiver(user_login_failed)
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """
    Handle failed login attempts
    """
    email = credentials.get('username')  # Django uses 'username' even for email
    
    if email:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Log failed attempt
        LoginAttempt.objects.create(
            email=email,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=False,
            failure_reason='Invalid credentials'
        )
        
        # Try to get user and increment failed attempts
        try:
            user = User.objects.get(email__iexact=email)
            old_attempts = user.failed_login_attempts
            user.increment_failed_attempts()
            
            # Send notification if account just got locked
            if old_attempts < 5 and user.failed_login_attempts >= 5:
                print("Account locked due to too many failed login attempts.")
                
        except User.DoesNotExist:
            pass