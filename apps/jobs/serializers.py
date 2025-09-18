from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .models import (
    Job, JobApplication, SavedJob, JobView, JobAlert, 
    JobCategory, JobType, Industry, Skill, Company
)

User = get_user_model()

class SkillSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=None, allow_null=True, required=False, read_only=True)
    popularity_score = serializers.IntegerField(read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import SkillCategory
        self.fields['category'].queryset = SkillCategory.active.all()

class IndustrySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    icon = serializers.CharField(max_length=50, required=False, allow_blank=True)
    job_count = serializers.SerializerMethodField()
    
    def get_job_count(self, obj):
        return obj.get_job_count()

class JobCategorySerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    slug = serializers.SlugField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=None, allow_null=True, required=False, read_only=True)
    icon = serializers.CharField(max_length=50, required=False, allow_blank=True)
    subcategories = serializers.SerializerMethodField()
    job_count = serializers.SerializerMethodField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = JobCategory.active.all()
    
    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return JobCategorySerializer(obj.subcategories.all(), many=True).data
        return []
    
    def get_job_count(self, obj):
        return obj.get_job_count()

class JobTypeSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=50)
    slug = serializers.SlugField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)

class CompanyMinimalSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    slug = serializers.SlugField(read_only=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    location = serializers.CharField(max_length=200)
    company_size = serializers.ChoiceField(choices=Company.COMPANY_SIZES, required=False, allow_null=True)
    is_verified = serializers.BooleanField(read_only=True)

class JobListSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=200)
    slug = serializers.SlugField(read_only=True)
    company = CompanyMinimalSerializer(read_only=True)
    category = JobCategorySerializer(read_only=True)
    industry = IndustrySerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    job_type = serializers.ChoiceField(choices=Job.JOB_TYPES)
    experience_level = serializers.ChoiceField(choices=Job.EXPERIENCE_LEVELS)
    location = serializers.CharField(max_length=200)
    remote_allowed = serializers.BooleanField()
    salary_range_display = serializers.ReadOnlyField()
    status = serializers.ChoiceField(choices=Job.STATUS_CHOICES, read_only=True)
    is_featured = serializers.BooleanField(read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    application_deadline = serializers.DateTimeField(required=False, allow_null=True)
    views_count = serializers.IntegerField(read_only=True)
    applications_count = serializers.IntegerField(read_only=True)
    days_since_posted = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    is_saved = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True)
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(user=request.user).exists()
        return False
    
    def get_has_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.applications.filter(applicant=request.user).exists()
        return False

class JobDetailSerializer(JobListSerializer):
    description = serializers.CharField()
    requirements = serializers.CharField()
    responsibilities = serializers.CharField()
    benefits = serializers.CharField(required=False, allow_blank=True)
    salary_min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    salary_max = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    salary_currency = serializers.ChoiceField(choices=Job.CURRENCY_CHOICES)
    salary_negotiable = serializers.BooleanField()
    start_date = serializers.DateField(required=False, allow_null=True)
    similar_jobs = serializers.SerializerMethodField()
    
    def get_similar_jobs(self, obj):
        similar = obj.get_similar_jobs()
        return JobListSerializer(similar, many=True, context=self.context).data

class JobCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    requirements = serializers.CharField()
    responsibilities = serializers.CharField()
    benefits = serializers.CharField(required=False, allow_blank=True)
    category = serializers.PrimaryKeyRelatedField(queryset=None, allow_null=True, required=False, read_only=True)
    industry = serializers.PrimaryKeyRelatedField(queryset=None, allow_null=True, required=False, read_only=True)
    skills = serializers.PrimaryKeyRelatedField(queryset=None, many=True, required=False, read_only=True)
    job_type = serializers.ChoiceField(choices=Job.JOB_TYPES)
    experience_level = serializers.ChoiceField(choices=Job.EXPERIENCE_LEVELS)
    location = serializers.CharField(max_length=200)
    remote_allowed = serializers.BooleanField(default=False)
    salary_min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    salary_max = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    salary_currency = serializers.ChoiceField(choices=Job.CURRENCY_CHOICES, default='USD')
    salary_negotiable = serializers.BooleanField(default=False)
    application_deadline = serializers.DateTimeField(required=False, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    is_featured = serializers.BooleanField(default=False)
    is_urgent = serializers.BooleanField(default=False)
    status = serializers.ChoiceField(choices=Job.STATUS_CHOICES, default='draft')

    class Meta:
        model = Job
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = JobCategory.active.all()
        self.fields['industry'].queryset = Industry.active.all()
        self.fields['skills'].queryset = Skill.active.all()
    
    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                "Minimum salary cannot be greater than maximum salary"
            )
        
        application_deadline = attrs.get('application_deadline')
        if application_deadline and application_deadline <= timezone.now():
            raise serializers.ValidationError(
                "Application deadline must be in the future"
            )
        
        return attrs
    
    def create(self, validated_data):
        skills_data = validated_data.pop('skills', [])
        job = Job.objects.create(**validated_data)
        job.skills.set(skills_data)
        return job
    
    def update(self, instance, validated_data):
        skills_data = validated_data.pop('skills', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if skills_data is not None:
            instance.skills.set(skills_data)
        
        return instance

class JobApplicationCreateSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    cover_letter = serializers.CharField(required=False, allow_blank=True)
    resume = serializers.FileField(required=False, allow_null=True)
    
    def validate_job(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This job is no longer accepting applications")
        return value
    
    def validate(self, attrs):
        user = self.context['request'].user
        job = attrs['job']
        
        if JobApplication.objects.filter(job=job, applicant=user).exists():
            raise serializers.ValidationError("You have already applied to this job")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return JobApplication.objects.create(**validated_data)

class JobApplicationDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    job = JobListSerializer(read_only=True)
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    applicant_email = serializers.CharField(source='applicant.email', read_only=True)
    cover_letter = serializers.CharField(required=False, allow_blank=True)
    resume = serializers.FileField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=JobApplication.STATUS_CHOICES, read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True, read_only=True)
    score = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True, read_only=True)
    days_since_applied = serializers.ReadOnlyField()
    can_withdraw = serializers.ReadOnlyField()
    applied_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)

class JobApplicationUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=JobApplication.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    score = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    
    def validate_status(self, value):
        if self.instance and self.instance.status == 'withdrawn':
            raise serializers.ValidationError("Cannot modify withdrawn application")
        return value
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = timezone.now()
        instance.save()
        return instance

class SavedJobSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    job = JobListSerializer(read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    saved_at = serializers.DateTimeField(read_only=True)

class SavedJobCreateSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        user = self.context['request'].user
        job = attrs['job']
        
        if SavedJob.objects.filter(user=user, job=job).exists():
            raise serializers.ValidationError("Job is already saved")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return SavedJob.objects.create(**validated_data)

class JobAlertCreateUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    keywords = serializers.CharField(max_length=500, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    remote_only = serializers.BooleanField(default=False)
    job_types = serializers.PrimaryKeyRelatedField(queryset=None, many=True, required=False, read_only=True)
    categories = serializers.PrimaryKeyRelatedField(queryset=None, many=True, required=False, read_only=True)
    industries = serializers.PrimaryKeyRelatedField(queryset=None, many=True, required=False, read_only=True)
    skills = serializers.PrimaryKeyRelatedField(queryset=None, many=True, required=False, read_only=True)
    experience_levels = serializers.ListField(
        child=serializers.ChoiceField(choices=Job.EXPERIENCE_LEVELS),
        required=False,
        allow_empty=True
    )
    salary_min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    salary_currency = serializers.ChoiceField(choices=Job.CURRENCY_CHOICES, default='USD')
    frequency = serializers.ChoiceField(choices=JobAlert.FREQUENCY_CHOICES, default='weekly')
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = JobAlert
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job_types'].queryset = JobType.active.all()
        self.fields['categories'].queryset = JobCategory.active.all()
        self.fields['industries'].queryset = Industry.active.all()
        self.fields['skills'].queryset = Skill.active.all()
    
    def create(self, validated_data):
        many_to_many_fields = ['job_types', 'categories', 'industries', 'skills']
        m2m_data = {field: validated_data.pop(field, []) for field in many_to_many_fields}
        
        validated_data['user'] = self.context['request'].user
        alert = JobAlert.objects.create(**validated_data)
        
        for field, data in m2m_data.items():
            getattr(alert, field).set(data)
        
        return alert
    
    def update(self, instance, validated_data):
        many_to_many_fields = ['job_types', 'categories', 'industries', 'skills']
        m2m_data = {field: validated_data.pop(field, None) for field in many_to_many_fields}
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        for field, data in m2m_data.items():
            if data is not None:
                getattr(instance, field).set(data)
        
        return instance

class JobAlertDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=200)
    keywords = serializers.CharField(max_length=500, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    remote_only = serializers.BooleanField()
    job_types = JobTypeSerializer(many=True, read_only=True)
    categories = JobCategorySerializer(many=True, read_only=True)
    industries = IndustrySerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    experience_levels = serializers.ListField(child=serializers.CharField())
    salary_min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    salary_currency = serializers.ChoiceField(choices=Job.CURRENCY_CHOICES)
    frequency = serializers.ChoiceField(choices=JobAlert.FREQUENCY_CHOICES)
    is_active = serializers.BooleanField()
    matching_jobs_count = serializers.SerializerMethodField()
    last_sent = serializers.DateTimeField(read_only=True)
    jobs_sent_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def get_matching_jobs_count(self, obj):
        return obj.get_matching_jobs().count()

class JobViewCreateSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    duration = serializers.IntegerField(required=False, allow_null=True)
    referrer = serializers.URLField(required=False, allow_null=True)
    
    def create(self, validated_data):
        request = self.context['request']
        validated_data.update({
            'user': request.user if request.user.is_authenticated else None,
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_key': request.session.session_key,
        })
        return JobView.objects.create(**validated_data)

class BulkJobStatusUpdateSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    status = serializers.ChoiceField(choices=Job.STATUS_CHOICES)
    
    def validate_job_ids(self, value):
        user = self.context['request'].user
        
        # Check if user owns all jobs or is admin
        if not user.is_admin():
            user_jobs = set(
                Job.objects.filter(created_by=user).values_list('id', flat=True)
            )
            if not set(value).issubset(user_jobs):
                raise serializers.ValidationError(
                    "You can only update jobs you created"
                )
        
        return value
    
    def update_jobs(self):
        job_ids = self.validated_data['job_ids']
        status = self.validated_data['status']
        
        with transaction.atomic():
            updated_count = Job.objects.filter(id__in=job_ids).update(status=status)
            if status == 'published':
                Job.objects.filter(
                    id__in=job_ids,
                    published_at__isnull=True
                ).update(published_at=timezone.now())
        
        return updated_count

class JobStatsSerializer(serializers.Serializer):
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    featured_jobs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    avg_applications_per_job = serializers.FloatField()
    total_views = serializers.IntegerField()
    avg_views_per_job = serializers.FloatField()
