# apps/jobs/tasks.py
from celery import shared_task
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
import logging
from .models import Job, JobApplication, JobAlert, JobView, Skill
from apps.core.utils import get_site_url
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

# Job Publishing Tasks
@shared_task(bind=True, max_retries=3)
def send_job_published_notification(self, job_id):
    """Send notification when job is published"""
    try:
        job = Job.objects.select_related('company', 'created_by').get(id=job_id)
        
        subject = f'Job Published: {job.title}'
        context = {
            'job': job,
            'site_url': get_site_url(),
            'job_url': f"{get_site_url()}/jobs/{job.slug}/"
        }
        
        html_message = render_to_string('emails/job_published.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[job.created_by.email],
            fail_silently=False
        )
        
        logger.info(f"Job published notification sent for job {job_id}")
        
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found for published notification")
    except Exception as exc:
        logger.error(f"Error sending job published notification: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_job_expiration_warning(self, job_id, days_until_expiration):
    """Send warning when job is about to expire"""
    try:
        job = Job.objects.select_related('company', 'created_by').get(id=job_id)
        
        subject = f'Job Expiring Soon: {job.title}'
        context = {
            'job': job,
            'days_until_expiration': days_until_expiration,
            'site_url': get_site_url(),
            'job_url': f"{get_site_url()}/jobs/{job.slug}/",
            'edit_url': f"{get_site_url()}/employer/jobs/{job.id}/edit/"
        }
        
        html_message = render_to_string('emails/job_expiration_warning.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[job.created_by.email],
            fail_silently=False
        )
        
        logger.info(f"Job expiration warning sent for job {job_id}")
        
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found for expiration warning")
    except Exception as exc:
        logger.error(f"Error sending job expiration warning: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

# Job Application Tasks
@shared_task(bind=True, max_retries=3)
def send_application_received_notification(self, application_id):
    """Send notification to employer when application is received"""
    try:
        application = JobApplication.objects.select_related(
            'job', 'job__company', 'job__created_by', 'applicant'
        ).get(id=application_id)
        
        # Notification to employer
        subject = f'New Application: {application.job.title}'
        context = {
            'application': application,
            'job': application.job,
            'applicant': application.applicant,
            'site_url': get_site_url(),
            'application_url': f"{get_site_url()}/employer/applications/{application.id}/"
        }
        
        html_message = render_to_string('emails/application_received_employer.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.job.created_by.email],
            fail_silently=False
        )
        
        # Confirmation to applicant
        subject = f'Application Submitted: {application.job.title}'
        context['application_url'] = f"{get_site_url()}/applications/{application.id}/"
        
        html_message = render_to_string('emails/application_submitted_applicant.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            fail_silently=False
        )
        
        logger.info(f"Application notifications sent for application {application_id}")
        
    except JobApplication.DoesNotExist:
        logger.error(f"Application {application_id} not found")
    except Exception as exc:
        logger.error(f"Error sending application notifications: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_application_status_update(self, application_id, old_status, new_status):
    """Send notification when application status changes"""
    try:
        application = JobApplication.objects.select_related(
            'job', 'job__company', 'applicant', 'reviewed_by'
        ).get(id=application_id)
        
        # Skip notification for certain status changes
        skip_statuses = ['pending', 'withdrawn']
        if new_status in skip_statuses:
            return
        
        subject = f'Application Update: {application.job.title}'
        context = {
            'application': application,
            'job': application.job,
            'old_status': old_status,
            'new_status': new_status,
            'status_display': dict(JobApplication.STATUS_CHOICES)[new_status],
            'site_url': get_site_url(),
            'application_url': f"{get_site_url()}/applications/{application.id}/"
        }
        
        html_message = render_to_string('emails/application_status_update.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            fail_silently=False
        )
        
        logger.info(f"Application status update sent for application {application_id}")
        
    except JobApplication.DoesNotExist:
        logger.error(f"Application {application_id} not found for status update")
    except Exception as exc:
        logger.error(f"Error sending application status update: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

# Job Alert Tasks
@shared_task
def send_job_alerts():
    """Send job alerts to users based on their criteria"""
    try:
        # Get all active job alerts
        alerts = JobAlert.objects.filter(is_active=True).select_related('user')
        
        for alert in alerts:
            if alert.should_send_alert():
                send_individual_job_alert.delay(alert.id)
        
        logger.info(f"Processed {alerts.count()} job alerts")
        
    except Exception as exc:
        logger.error(f"Error processing job alerts: {str(exc)}")

@shared_task(bind=True, max_retries=3)
def send_individual_job_alert(self, alert_id):
    """Send individual job alert to user"""
    try:
        alert = JobAlert.objects.select_related('user').get(id=alert_id)
        matching_jobs = alert.get_matching_jobs()
        
        # Get new jobs since last alert
        if alert.last_sent:
            matching_jobs = matching_jobs.filter(published_at__gt=alert.last_sent)
        
        matching_jobs = matching_jobs[:20]  # Limit to 20 jobs per alert
        
        if not matching_jobs:
            return
        
        subject = f'Job Alert: {alert.name} - {matching_jobs.count()} new jobs'
        context = {
            'alert': alert,
            'jobs': matching_jobs,
            'jobs_count': matching_jobs.count(),
            'site_url': get_site_url(),
            'unsubscribe_url': f"{get_site_url()}/alerts/{alert.id}/unsubscribe/"
        }
        
        html_message = render_to_string('emails/job_alert.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[alert.user.email],
            fail_silently=False
        )
        
        # Mark alert as sent
        alert.mark_as_sent(matching_jobs.count())
        
        logger.info(f"Job alert sent to {alert.user.email} with {matching_jobs.count()} jobs")
        
    except JobAlert.DoesNotExist:
        logger.error(f"Job alert {alert_id} not found")
    except Exception as exc:
        logger.error(f"Error sending job alert {alert_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

# Periodic Tasks
@shared_task
def check_job_expiration():
    """Check for jobs nearing expiration and send warnings"""
    try:
        now = timezone.now()
        
        # Jobs expiring in 3 days
        three_days = now + timedelta(days=3)
        expiring_jobs_3d = Job.objects.filter(
            status='published',
            application_deadline__lte=three_days,
            application_deadline__gt=now + timedelta(days=2)
        )
        
        for job in expiring_jobs_3d:
            send_job_expiration_warning.delay(job.id, 3)
        
        # Jobs expiring in 1 day
        one_day = now + timedelta(days=1)
        expiring_jobs_1d = Job.objects.filter(
            status='published',
            application_deadline__lte=one_day,
            application_deadline__gt=now
        )
        
        for job in expiring_jobs_1d:
            send_job_expiration_warning.delay(job.id, 1)
        
        # Auto-close expired jobs
        expired_jobs = Job.objects.filter(
            status='published',
            application_deadline__lt=now
        )
        
        expired_count = expired_jobs.update(status='closed')
        
        logger.info(f"Job expiration check completed. Expired {expired_count} jobs")
        
    except Exception as exc:
        logger.error(f"Error in job expiration check: {str(exc)}")

@shared_task
def cleanup_old_job_views():
    """Clean up old job view records"""
    try:
        # Remove job views older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = JobView.objects.filter(viewed_at__lt=cutoff_date).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old job view records")
        
    except Exception as exc:
        logger.error(f"Error cleaning up job views: {str(exc)}")

@shared_task
def update_job_stats():
    """Update job statistics and popularity scores"""
    try:
        # Update skill popularity scores
        from .models import Skill
        skills = Skill.objects.all()
        
        for skill in skills:
            skill.update_popularity_score()
        
        logger.info(f"Updated popularity scores for {skills.count()} skills")
        
    except Exception as exc:
        logger.error(f"Error updating job stats: {str(exc)}")

@shared_task
def generate_weekly_reports():
    """Generate weekly reports for employers"""
    try:
        # Get all employers with active jobs
        employers = User.objects.filter(
            role='employer',
            created_jobs__status='published'
        ).distinct()
        
        for employer in employers:
            generate_employer_weekly_report.delay(employer.id)
        
        logger.info(f"Initiated weekly reports for {employers.count()} employers")
        
    except Exception as exc:
        logger.error(f"Error generating weekly reports: {str(exc)}")

@shared_task(bind=True, max_retries=3)
def generate_employer_weekly_report(self, employer_id):
    """Generate weekly report for individual employer"""
    try:
        employer = User.objects.get(id=employer_id)
        
        # Get stats for the past week
        week_ago = timezone.now() - timedelta(days=7)
        
        jobs = Job.objects.filter(created_by=employer, status='published')
        
        stats = {
            'total_jobs': jobs.count(),
            'new_applications': JobApplication.objects.filter(
                job__created_by=employer,
                applied_at__gte=week_ago
            ).count(),
            'total_views': sum(job.views_count for job in jobs),
            'new_views': JobView.objects.filter(
                job__created_by=employer,
                viewed_at__gte=week_ago
            ).count(),
        }
        
        # Get top performing jobs
        top_jobs = jobs.annotate(
            weekly_applications=Count(
                'applications',
                filter=Q(applications__applied_at__gte=week_ago)
            )
        ).order_by('-weekly_applications')[:5]
        
        subject = 'Weekly Job Performance Report'
        context = {
            'employer': employer,
            'stats': stats,
            'top_jobs': top_jobs,
            'week_start': week_ago.strftime('%B %d, %Y'),
            'site_url': get_site_url()
        }
        
        html_message = render_to_string('emails/weekly_report.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[employer.email],
            fail_silently=False
        )
        
        logger.info(f"Weekly report sent to employer {employer_id}")
        
    except User.DoesNotExist:
        logger.error(f"Employer {employer_id} not found for weekly report")
    except Exception as exc:
        logger.error(f"Error generating weekly report for employer {employer_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

# Bulk Operations
@shared_task
def bulk_job_status_update(job_ids, status, user_id):
    """Bulk update job status"""
    try:
        updated_count = Job.objects.filter(id__in=job_ids).update(status=status)
        
        # If publishing jobs, set published_at
        if status == 'published':
            Job.objects.filter(
                id__in=job_ids,
                published_at__isnull=True
            ).update(published_at=timezone.now())
        
        # Send notifications for published jobs
        if status == 'published':
            for job_id in job_ids:
                send_job_published_notification.delay(job_id)
        
        logger.info(f"Bulk updated {updated_count} jobs to status {status}")
        return updated_count
        
    except Exception as exc:
        logger.error(f"Error in bulk job status update: {str(exc)}")
        return 0

@shared_task
def send_bulk_email_to_applicants(job_id, subject, message, sender_id):
    """Send bulk email to all applicants of a job"""
    try:
        job = Job.objects.get(id=job_id)
        sender = User.objects.get(id=sender_id)
        
        # Get all applicants for this job
        applicants = User.objects.filter(
            applications__job=job
        ).distinct().values_list('email', flat=True)
        
        if not applicants:
            return
        
        # Prepare mass email
        messages = []
        for email in applicants:
            context = {
                'job': job,
                'sender': sender,
                'message': message,
                'site_url': get_site_url()
            }
            
            html_message = render_to_string('emails/bulk_message.html', context)
            plain_message = strip_tags(html_message)
            
            messages.append((
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email]
            ))
        
        # Send mass email
        send_mass_mail(messages, fail_silently=False)
        
        logger.info(f"Bulk email sent to {len(messages)} applicants for job {job_id}")
        
    except (Job.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Job or user not found for bulk email: {str(e)}")
    except Exception as exc:
        logger.error(f"Error sending bulk email: {str(exc)}")

# Analytics Tasks
@shared_task
def generate_job_analytics():
    """Generate analytics data for jobs"""
    try:
        from django.core.cache import cache
        
        # Calculate various metrics
        metrics = {
            'total_jobs': Job.objects.filter(status='published').count(),
            'total_applications': JobApplication.objects.count(),
            'active_users': User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count(),
            'top_skills': list(Skill.objects.order_by('-popularity_score')[:10].values('name', 'popularity_score')),
            'jobs_by_type': dict(Job.objects.filter(status='published').values_list('job_type').annotate(Count('job_type'))),
        }
        
        # Cache the metrics for 1 hour
        cache.set('job_analytics', metrics, 3600)
        
        logger.info("Job analytics generated and cached")
        
    except Exception as exc:
        logger.error(f"Error generating job analytics: {str(exc)}")

# Error Handling and Retry Tasks
@shared_task(bind=True, max_retries=5)
def retry_failed_email(self, email_data):
    """Retry failed email sending"""
    try:
        send_mail(**email_data)
        logger.info("Failed email retry successful")
        
    except Exception as exc:
        logger.error(f"Email retry failed: {str(exc)}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        else:
            logger.error(f"Email permanently failed after {self.max_retries} retries")