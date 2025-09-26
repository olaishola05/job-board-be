from django.contrib import admin
from django.contrib import messages
from .tasks import (
    send_job_published_notification, 
    bulk_job_status_update,
)

class JobAdmin(admin.ModelAdmin):
    actions = ['publish_jobs', 'close_jobs', 'send_notifications']
    
    def publish_jobs(self, request, queryset):
        job_ids = [job.id for job in queryset]
        bulk_job_status_update.delay(job_ids, 'published', request.user.user)
        messages.success(request, f'{len(job_ids)} jobs queued for publishing')
    
    def close_jobs(self, request, queryset):
        job_ids = [job.id for job in queryset]
        bulk_job_status_update.delay(job_ids, 'closed', request.user.user)
        messages.success(request, f'{len(job_ids)} jobs queued for closing')
    
    def send_notifications(self, request, queryset):
        for job in queryset.filter(status='published'):
            send_job_published_notification.delay(job.id)
        messages.success(request, f'Notifications queued for {queryset.count()} jobs')