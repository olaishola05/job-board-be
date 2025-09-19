# apps/companies/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Company, CompanyFollow, CompanyReview, CompanyAnalytics, CompanyMedia

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'location', 'industry', 'company_size', 'approval_status',
        'is_verified', 'is_featured', 'rating', 'job_count', 'follower_count',
        'view_count', 'created_at'
    ]
    list_filter = [
        'approval_status', 'is_verified', 'is_featured', 'company_size',
        'industry', 'created_at'
    ]
    search_fields = ['name', 'description', 'location', 'website']
    readonly_fields = [
        'slug', 'created_at', 'updated_at', 'rating', 'review_count',
        'follower_count', 'job_count', 'view_count', 'company_logo_preview'
    ]
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_verified', 'is_featured', 'approval_status']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'slug', 'description', 'website', 'email', 'phone'
            )
        }),
        ('Media', {
            'fields': ('logo', 'company_logo_preview', 'banner')
        }),
        ('Company Details', {
            'fields': (
                'founded_year', 'company_size', 'employee_count', 'industry'
            )
        }),
        ('Location', {
            'fields': (
                'location', 'address', 'city', 'state', 'country',
                'postal_code', 'latitude', 'longitude'
            )
        }),
        ('Status & Verification', {
            'fields': (
                'created_by', 'approval_status', 'is_verified', 'is_featured',
                'is_active', 'approved_at'
            )
        }),
        ('Metrics', {
            'fields': (
                'rating', 'review_count', 'follower_count', 'job_count',
                'view_count'
            ),
            'classes': ('collapse',)
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'twitter_url', 'facebook_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def company_logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;">',
                obj.logo.url
            )
        return "No logo"
    company_logo_preview.short_description = "Logo Preview"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('industry', 'created_by').annotate(
            job_count=Count('jobs')
        )
    
    actions = ['approve_companies', 'reject_companies', 'feature_companies']
    
    def approve_companies(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(
            approval_status='approved',
            is_verified=True,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} companies approved successfully.')
    approve_companies.short_description = "Approve selected companies"
    
    def reject_companies(self, request, queryset):
        count = queryset.update(
            approval_status='rejected',
            is_verified=False
        )
        self.message_user(request, f'{count} companies rejected.')
    reject_companies.short_description = "Reject selected companies"
    
    def feature_companies(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} companies featured.')
    feature_companies.short_description = "Feature selected companies"

@admin.register(CompanyFollow)
class CompanyFollowAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'followed_at', 'notifications_enabled']
    list_filter = ['notifications_enabled', 'followed_at']
    search_fields = ['user__email', 'company__name']
    raw_id_fields = ['user', 'company']
    date_hierarchy = 'followed_at'

@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'user_display', 'rating', 'title', 'employment_status',
        'is_anonymous', 'created_at'
    ]
    list_filter = [
        'rating', 'employment_status', 'is_anonymous', 'is_current_employee',
        'created_at'
    ]
    search_fields = ['company__name', 'user__email', 'title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['company', 'user']
    date_hierarchy = 'created_at'
    
    def user_display(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.user.get_full_name() or obj.user.email
    user_display.short_description = "User"

@admin.register(CompanyAnalytics)
class CompanyAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'total_views', 'monthly_views', 'total_applications',
        'bounce_rate', 'last_updated'
    ]
    list_filter = ['last_updated']
    search_fields = ['company__name']
    readonly_fields = [
        'total_views', 'monthly_views', 'total_job_views', 'total_applications',
        'avg_time_on_page', 'bounce_rate', 'top_referrers', 'monthly_stats',
        'last_updated'
    ]
    raw_id_fields = ['company']

@admin.register(CompanyMedia)
class CompanyMediaAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'title', 'media_type', 'is_featured', 'uploaded_by', 'created_at'
    ]
    list_filter = ['media_type', 'is_featured', 'created_at']
    search_fields = ['company__name', 'title']
    readonly_fields = ['created_at', 'media_preview']
    raw_id_fields = ['company', 'uploaded_by']
    
    def media_preview(self, obj):
        if obj.media_type == 'image' and obj.file:
            return format_html(
                '<img src="{}" width="200" height="200" style="object-fit: cover;">',
                obj.file.url
            )
        elif obj.thumbnail:
            return format_html(
                '<img src="{}" width="200" height="200" style="object-fit: cover;">',
                obj.thumbnail.url
            )
        return "No preview available"
    media_preview.short_description = "Media Preview"