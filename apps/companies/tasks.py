from celery import shared_task
from django.db.models import Count, Avg, F
from django.utils import timezone
from datetime import timedelta
from .models import Company, CompanyAnalytics
from apps.jobs.models import Job, JobApplication
from apps.core.utils import send_email
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def notify_company_creation(company_id):
    """Notify admin about new company creation"""
    try:
        company = Company.objects.get(id=company_id)
        context = {'company': company, 'site_name': 'Job Board'}
        if company.created_by and company.created_by.email:
            send_email(
                to_email=company.created_by.email,
                template='emails/company_created.html',
                context=context,
                subject='Your company has been created!'
            )
    except Company.DoesNotExist:
        print(f"Company with ID {company_id} does not exist.")

@shared_task
def send_company_approved_email(company_id):
    """Send email notification when a company is approved"""
    try:
        company = Company.objects.get(id=company_id)
        if company.is_verified and company.created_by and company.created_by.email:
            send_email(
                to_email=company.created_by.email,
                template='emails/company_approved.html',
                context={'company': company},
                subject='Your company has been approved!'
            )
    except Company.DoesNotExist:
        print(f"Company with ID {company_id} does not exist.")
        
@shared_task
def notify_company_rejection(company_id, reason):
    """Notify company creator about rejection"""
    try:
        company = Company.objects.get(id=company_id)
        if company.created_by and company.created_by.email:
            send_email(
                to_email=company.created_by.email,
                template='emails/company_rejected.html',
                context={'company': company, 'reason': reason},
                subject='Your company has been rejected'
            )
    except Company.DoesNotExist:
        print(f"Company with ID {company_id} does not exist.")

@shared_task
def update_company_analytics():
    """Update company analytics data"""
    for company in Company.objects.filter(is_active=True):
        analytics, created = CompanyAnalytics.objects.get_or_create(
            company=company,
            defaults={
                'total_views': company.view_count,
                'monthly_views': 0,
                'total_job_views': 0,
                'total_applications': 0,
            }
        )
        
        jobs = Job.objects.filter(company=company)
        analytics.total_job_views = sum(job.views_count for job in jobs)
        analytics.total_applications = JobApplication.objects.filter(job__company=company).count()
        analytics.save()

@shared_task
def send_job_notification_email(user_id, job_id):
    """Send job notification email to user"""
    try:
        
        user = User.objects.get(id=user_id)
        job = Job.objects.get(id=job_id)
        
        context = {
            'user': user,
            'job': job,
            'company': job.company,
        }
        
        send_email(
            to_email=user.email,
            template='emails/job_notification.html',
            context=context,
            subject=f'New job at {job.company.name}: {job.title}'
        )
    except Exception as e:
        print(f"Failed to send job notification: {e}")

@shared_task
def cleanup_old_analytics():
    """Clean up old analytics data"""
    cutoff_date = timezone.now() - timedelta(days=365)
    old_analytics = CompanyAnalytics.objects.filter(
        company__created_at__lt=cutoff_date
    )
    old_analytics.delete()

@shared_task
def generate_company_reports():
    """Generate monthly company performance reports"""
    
    # Generate reports for companies
    companies = Company.objects.filter(
        is_verified=True,
        created_by__is_active=True
    ).select_related('created_by', 'analytics')
    
    for company in companies:
        try:
            analytics = company.analytics
            report_data = {
                'company': company,
                'total_views': analytics.total_views,
                'monthly_views': analytics.monthly_views,
                'applications': analytics.total_applications,
                'jobs_count': company.jobs.filter(status='published').count(),
            }
            
            context = {'company': company, 'report': report_data}

            send_email(
                subject=f'Monthly Report for {company.name}',
                template='emails/company_monthly_report.html',
                context=context,
                to_email=[company.created_by.email],
            )
        except Exception as e:
            print(f"Failed to generate report for {company.name}: {e}")