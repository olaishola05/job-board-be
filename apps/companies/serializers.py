from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from django.db import models
from django.utils import timezone
from .models import Company, CompanyFollow, CompanyReview, CompanyAnalytics, CompanyMedia
from apps.jobs.serializers import IndustrySerializer
from apps.accounts.serializers import UserSerializer

class CompanyListSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    job_count = SerializerMethodField()
    follower_count = SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'logo', 'location', 'company_size',
            'industry_name', 'is_verified', 'is_featured', 'rating',
            'job_count', 'follower_count', 'created_at'
        ]
    
    def get_job_count(self, obj):
        return getattr(obj, 'active_job_count', obj.job_count)
    
    def get_follower_count(self, obj):
        return getattr(obj, 'total_followers', obj.follower_count)

class CompanyDetailSerializer(serializers.ModelSerializer):
    industry = IndustrySerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    is_following = SerializerMethodField()
    job_stats = SerializerMethodField()
    media_gallery = SerializerMethodField()
    recent_reviews = SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'description', 'website', 'email', 'phone',
            'logo', 'banner', 'founded_year', 'company_size', 'employee_count',
            'industry', 'location', 'address', 'city', 'state', 'country',
            'is_verified', 'is_featured', 'rating', 'review_count',
            'follower_count', 'job_count', 'linkedin_url', 'twitter_url',
            'facebook_url', 'created_by', 'created_at', 'is_following',
            'job_stats', 'media_gallery', 'recent_reviews'
        ]
        read_only_fields = [
            'slug', 'rating', 'review_count', 'follower_count', 'job_count',
            'is_verified', 'created_by', 'created_at'
        ]
    
    def get_is_following(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return CompanyFollow.objects.filter(company=obj, user=user).exists()
        return False
    
    def get_job_stats(self, obj):
        from apps.jobs.models import Job
        jobs = Job.objects.filter(company=obj, status='published')
        return {
            'total_jobs': jobs.count(),
            'active_jobs': jobs.filter(
                models.Q(application_deadline__isnull=True) |
                models.Q(application_deadline__gt=timezone.now())
            ).count(),
            'job_types': list(jobs.values_list('job_type', flat=True).distinct()),
            'avg_salary': obj.average_salary
        }
    
    def get_media_gallery(self, obj):
        return CompanyMediaSerializer(
            obj.media.filter(is_featured=True)[:6], many=True
        ).data
    
    def get_recent_reviews(self, obj):
        return CompanyReviewSerializer(
            obj.reviews.select_related('user')[:3], many=True
        ).data

class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'name', 'description', 'website', 'email', 'phone', 'logo', 'banner',
            'founded_year', 'company_size', 'employee_count', 'industry',
            'location', 'address', 'city', 'state', 'country', 'postal_code',
            'linkedin_url', 'twitter_url', 'facebook_url'
        ]
    
    def validate_name(self, value):
        instance = getattr(self, 'instance', None)
        if Company.objects.filter(name__iexact=value).exclude(pk=instance.pk if instance else None).exists():
            raise serializers.ValidationError("Company with this name already exists.")
        return value
    
    def validate_founded_year(self, value):
        from django.utils import timezone
        if value and value > timezone.now().year:
            raise serializers.ValidationError("Founded year cannot be in the future.")
        return value
    
    def validate_employee_count(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Employee count must be at least 1.")
        return value

class CompanyAnalyticsSerializer(serializers.ModelSerializer):
    performance_metrics = SerializerMethodField()
    traffic_sources = SerializerMethodField()
    
    class Meta:
        model = CompanyAnalytics
        fields = [
            'total_views', 'monthly_views', 'total_job_views', 'total_applications',
            'avg_time_on_page', 'bounce_rate', 'performance_metrics',
            'traffic_sources', 'monthly_stats', 'last_updated'
        ]
    
    def get_performance_metrics(self, obj):
        company = obj.company
        return {
            'profile_completion': self._calculate_completion(company),
            'engagement_rate': self._calculate_engagement(obj),
            'conversion_rate': self._calculate_conversion(obj)
        }
    
    def get_traffic_sources(self, obj):
        return obj.top_referrers or {}
    
    def _calculate_completion(self, company):
        fields = ['description', 'website', 'logo', 'founded_year', 'industry']
        completed = sum(1 for field in fields if getattr(company, field))
        return int((completed / len(fields)) * 100)
    
    def _calculate_engagement(self, analytics):
        if analytics.total_views == 0:
            return 0
        return round((analytics.total_applications / analytics.total_views) * 100, 2)
    
    def _calculate_conversion(self, analytics):
        if analytics.total_job_views == 0:
            return 0
        return round((analytics.total_applications / analytics.total_job_views) * 100, 2)

class CompanyFollowSerializer(serializers.ModelSerializer):
    company = CompanyListSerializer(read_only=True)
    
    class Meta:
        model = CompanyFollow
        fields = ['company', 'followed_at', 'notifications_enabled']
        read_only_fields = ['followed_at']

class CompanyReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_display_name = SerializerMethodField()
    
    class Meta:
        model = CompanyReview
        fields = [
            'id', 'rating', 'title', 'content', 'pros', 'cons',
            'is_anonymous', 'is_current_employee', 'job_title',
            'employment_status', 'user', 'user_display_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_user_display_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.user.get_full_name() or obj.user.username

class CompanyReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyReview
        fields = [
            'rating', 'title', 'content', 'pros', 'cons', 'is_anonymous',
            'is_current_employee', 'job_title', 'employment_status'
        ]
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

class CompanyMediaSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyMedia
        fields = [
            'id', 'title', 'description', 'media_type', 'file_url',
            'thumbnail_url', 'order', 'is_featured', 'uploaded_by', 'created_at'
        ]
        read_only_fields = ['uploaded_by', 'created_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.thumbnail.url) if request else obj.thumbnail.url
        return None

class CompanySearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, help_text="Search term")
    industry = serializers.UUIDField(required=False, help_text="Industry ID")
    location = serializers.CharField(required=False, help_text="Location")
    company_size = serializers.ChoiceField(
        choices=Company.COMPANY_SIZES, required=False
    )
    is_verified = serializers.BooleanField(required=False)
    is_featured = serializers.BooleanField(required=False)
    min_rating = serializers.DecimalField(
        max_digits=3, decimal_places=2, required=False,
        min_value=0, max_value=5
    )
    founded_year_min = serializers.IntegerField(required=False)
    founded_year_max = serializers.IntegerField(required=False)
    ordering = serializers.ChoiceField(
        choices=[
            'name', '-name', 'created_at', '-created_at', 'rating', '-rating',
            'follower_count', '-follower_count', 'job_count', '-job_count'
        ],
        required=False,
        default='-created_at'
    )

class CompanyStatsSerializer(serializers.Serializer):
    total_companies = serializers.IntegerField()
    verified_companies = serializers.IntegerField()
    featured_companies = serializers.IntegerField()
    companies_with_jobs = serializers.IntegerField()
    top_industries = serializers.ListField()
    avg_company_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    monthly_growth = serializers.DecimalField(max_digits=5, decimal_places=2)