from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta
import logging
from .models import User

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user):
    """
    Send email verification link to user
    """
    try:
        user = User.objects.get(id=user)

        if user.is_verified:
            logger.info(f"User {user.email} is already verified")
            return f"User {user.email} is already verified"
        print(user.verification_token)
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={user.verification_token}"
        
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': getattr(settings, 'SITE_NAME', 'Job Board Platform'),
            'site_url': settings.FRONTEND_URL,
            'expiry_hours': 24
        }
        
        html_content = render_to_string('emails/verification.html', context)
        text_content = strip_tags(html_content)

        subject = f"Verify Your Email Address - {context['site_name']}"

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Verification email sent to {user.email}")
        return f"Verification email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user} not found")
        raise self.retry(countdown=60)
        
    except Exception as exc:
        logger.error(f"Failed to send verification email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id):
    """
    Send password reset link to user
    """
    try:      
        user = User.objects.get(id=user_id)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={user.password_reset_token}"
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': getattr(settings, 'SITE_NAME', 'Job Board Platform'),
            'site_url': settings.FRONTEND_URL,
            'expiry_hours': 24
        }
        
        html_content = render_to_string('emails/password_reset.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"Reset Your Password - {context['site_name']}"
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        
        logger.info(f"Password reset email sent to {user.email}")
        return f"Password reset email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        raise self.retry(countdown=60)
        
    except Exception as exc:
        logger.error(f"Failed to send password reset email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_password_change_confirmation(self, user_id):
    """
    Send password change confirmation email
    """
    try:
        user = User.objects.get(id=user_id)
        
        context = {
            'user': user,
            'site_name': getattr(settings, 'SITE_NAME', 'Job Board Platform'),
            'site_url': settings.FRONTEND_URL,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
        }
        
        html_content = render_to_string('emails/password_change_confirmation.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"Your Password Has Been Changed - {context['site_name']}"
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        
        logger.info(f"Password change confirmation email sent to {user.email}")
        return f"Password change confirmation email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        self.retry(countdown=60)
        
    except Exception as exc:
        logger.error(f"Failed to send password change confirmation email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """
    Send welcome email to newly verified user
    """
    try:
        
        user = User.objects.get(id=user_id)
        
        context = {
            'user': user,
            'site_name': getattr(settings, 'SITE_NAME', 'Job Board Platform'),
            'site_url': settings.FRONTEND_URL,
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
            'profile_url': f"{settings.FRONTEND_URL}/profile"
        }
        
        html_content = render_to_string('emails/welcome.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"Welcome to {context['site_name']}!"
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return f"Welcome email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        raise self.retry(countdown=60)
        
    except Exception as exc:
        logger.error(f"Failed to send welcome email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_account_locked_notification(self, user_id):
    """
    Send notification when account is locked
    """
    try:
        user = User.objects.get(id=user_id)
        
        context = {
            'user': user,
            'site_name': getattr(settings, 'SITE_NAME', 'Job Board Platform'),
            'site_url': settings.FRONTEND_URL,
            'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'locked_until': user.account_locked_until
        }
        
        html_content = render_to_string('emails/account_locked.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"Account Security Alert - {context['site_name']}"
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        
        logger.info(f"Account locked notification sent to {user.email}")
        return f"Account locked notification sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        raise self.retry(countdown=60)
        
    except Exception as exc:
        logger.error(f"Failed to send account locked notification: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired refresh tokens and verification tokens
    """
    try:
        from .models import RefreshToken
        
        expired_tokens = RefreshToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        expired_count = expired_tokens.count()
        expired_tokens.delete()
        
        cutoff_date = timezone.now() - timedelta(days=7)
        old_tokens = User.objects.filter(
            verification_token_created__lt=cutoff_date,
            verification_token__isnull=False
        )
        
        for user in old_tokens:
            user.clear_token('verification')
        
        logger.info(f"Cleaned up {expired_count} expired refresh tokens and old verification tokens")
        return f"Cleaned up {expired_count} expired tokens"
        
    except Exception as exc:
        logger.error(f"Failed to cleanup tokens: {str(exc)}")
        raise


@shared_task
def cleanup_unverified_users():
    """
    Clean up unverified users older than 30 days
    """
    try:
        count = User.objects.cleanup_unverified_users(days_old=30)
        
        logger.info(f"Cleaned up {count} unverified users")
        return f"Cleaned up {count} unverified users"
        
    except Exception as exc:
        logger.error(f"Failed to cleanup unverified users: {str(exc)}")
        raise


@shared_task
def generate_security_report():
    """
    Generate daily security report
    """
    try:
        from .models import LoginAttempt
        from django.db.models import Count
        
        # Get yesterday's date
        yesterday = timezone.now() - timedelta(days=1)
        today = timezone.now()
        
        # Login statistics
        total_attempts = LoginAttempt.objects.filter(
            timestamp__gte=yesterday,
            timestamp__lt=today
        ).count()
        
        successful_logins = LoginAttempt.objects.filter(
            timestamp__gte=yesterday,
            timestamp__lt=today,
            success=True
        ).count()
        
        failed_attempts = total_attempts - successful_logins
        
        # Failed attempts by IP
        failed_by_ip = LoginAttempt.objects.filter(
            timestamp__gte=yesterday,
            timestamp__lt=today,
            success=False
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Locked accounts
        locked_accounts = User.objects.filter(
            account_locked_until__isnull=False,
            account_locked_until__gt=timezone.now()
        ).count()
        
        # New registrations
        new_registrations = User.objects.filter(
            created_at__gte=yesterday,
            created_at__lt=today
        ).count()
        
        # Prepare report context
        context = {
            'date': yesterday.date(),
            'total_attempts': total_attempts,
            'successful_logins': successful_logins,
            'failed_attempts': failed_attempts,
            'failed_by_ip': failed_by_ip,
            'locked_accounts': locked_accounts,
            'new_registrations': new_registrations,
            'site_name': getattr(settings, 'SITE_NAME', 'Job Board Platform')
        }
        
        # Send report to admins
        admin_emails = User.objects.filter(
            role='admin',
            is_active=True
        ).values_list('email', flat=True)
        
        if admin_emails:
            # html_content = render_to_string('emails/security_report.html', context)
            # text_content = strip_tags(html_content)
            # 
            # subject = f"Daily Security Report - {context['site_name']}"
            # 
            # for admin_email in admin_emails:
                # msg = EmailMultiAlternatives(
                    # subject=subject,
                    # body=text_content,
                    # from_email=settings.DEFAULT_FROM_EMAIL,
                    # to=[admin_email]
                # )
                # msg.attach_alternative(html_content, "text/html")
                # msg.send()
                
                print(context)
        
        logger.info("Daily security report generated and sent")
        return "Daily security report generated and sent"
        
    except Exception as exc:
        logger.error(f"Failed to generate security report: {str(exc)}")
        raise


@shared_task
def unlock_accounts():
    """
    Unlock accounts that have passed their lock period
    """
    try:
        from .models import User
        
        # Find accounts that should be unlocked
        locked_users = User.objects.filter(
            account_locked_until__isnull=False,
            account_locked_until__lte=timezone.now()
        )
        
        count = 0
        for user in locked_users:
            user.unlock_account()
            count += 1
        
        logger.info(f"Unlocked {count} accounts")
        return f"Unlocked {count} accounts"
        
    except Exception as exc:
        logger.error(f"Failed to unlock accounts: {str(exc)}")
        raise