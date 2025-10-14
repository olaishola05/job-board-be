from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.pagination import CursorPagination, StandardPagination
from apps.core.permissions import IsEmployerOrReadOnly, IsAdminOrReadOnly
from apps.jobs.tests.test_jobs_views import company
from .models import (
    Job, JobApplication, SavedJob, JobView, JobAlert,
    JobCategory, JobType, Industry, Skill
)
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateUpdateSerializer,
    JobApplicationCreateSerializer, JobApplicationDetailSerializer, JobApplicationUpdateSerializer,
    SavedJobSerializer, SavedJobCreateSerializer, JobAlertCreateUpdateSerializer, JobAlertDetailSerializer, JobSearchSerializer,
    JobViewCreateSerializer, BulkJobStatusUpdateSerializer, JobStatsSerializer,
    JobCategorySerializer, JobTypeSerializer, IndustrySerializer, SkillSerializer, JobResultSerializer
)
from .filters import JobFilter, JobApplicationFilter
from .search import JobSearchEngine
from .tasks import send_application_received_notification, bulk_job_status_update
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related('company', 'category', 'industry', 'created_by').prefetch_related('skills')
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'description', 'requirements', 'company__name']
    ordering_fields = ['created_at', 'published_at', 'views_count', 'applications_count', 'application_deadline']
    ordering = ['-is_featured', '-published_at']
    
    def get_serializer_class(self): # type: ignore
        if self.action == 'list':
            return JobListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return JobCreateUpdateSerializer
        return JobDetailSerializer
    
    def get_queryset(self):
        queryset = self.queryset
        
        if self.action == 'list':
            if not (self.request.user.is_authenticated and 
                   (self.request.user.is_admin() or self.request.user.is_employer())):
                queryset = queryset.filter(status='published')
        
        if self.action in ['my_jobs', 'stats']:
            if self.request.user.is_authenticated:
                if self.request.user.is_employer():
                    queryset = queryset.filter(created_by=self.request.user)
                else:
                    queryset = queryset.none()
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
      user = self.request.user
      company = getattr(user, "companies", None).first() if hasattr(user, "companies") else None
      industry = company.industry if company else None
      category_id = serializer.validated_data.get('category')
      category = JobCategory.objects.filter(id=category_id.id).first() if category_id else None
      if company:
        serializer.save(
            created_by=user,
            company=company,
            industry=industry,
            category=category
        )
        
      else:
        serializer.save(created_by=user, industry=industry, category=category)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Track job view
        if not (request.user.is_authenticated and 
               (instance.created_by == request.user or request.user.is_admin())):
            JobView.objects.create(
                job=instance,
                user=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_key=request.session.session_key
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured jobs"""
        queryset = self.get_queryset().filter(is_featured=True, status='published')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = JobListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = JobListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsEmployerOrReadOnly])
    def my_jobs(self, request):
        """Get user's own job postings"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = JobListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = JobListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request, pk=None):
        """Apply to a job"""
        job = self.get_object()
        
        if JobApplication.objects.filter(job=job, applicant=request.user).exists():
            return Response(
                {'error': 'You have already applied to this job'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not job.is_active:
            return Response(
                {'error': 'This job is no longer accepting applications'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        data = request.data.copy()
        data['job'] = job.id

        serializer = JobApplicationCreateSerializer(
            data=data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            print("REQ DATA:", request.data)
            print("REQ FILES:", request.FILES)
            print("SER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        application = serializer.save()
        send_application_received_notification.delay(application.id)
        return Response(
            JobApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def save(self, request, pk=None):
        """Save/unsave a job"""
        job = self.get_object()
        
        if request.method == 'POST':
            serializer = SavedJobCreateSerializer(
                data={**request.data, 'job': job.id},
                context={'request': request}
            )
            if serializer.is_valid():
                saved_job = serializer.save()
                return Response(
                    SavedJobSerializer(saved_job, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            try:
                saved_job = SavedJob.objects.get(job=job, user=request.user)
                saved_job.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except SavedJob.DoesNotExist:
                return Response(
                    {'error': 'Job not found in saved jobs'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
    
    @action(detail=True, methods=['post'])
    def track_view(self, request, pk=None):
        """Track job view with additional data"""
        job = self.get_object()
        serializer = JobViewCreateSerializer(
            data={**request.data, 'job': job.id},
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_status_update(self, request):
        """Bulk update job status"""
        serializer = BulkJobStatusUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            updated_count = serializer.update_jobs()
            ob_ids = [str(id) for id in serializer.validated_data['job_ids']]
            status_value = serializer.validated_data['status']
            
            bulk_job_status_update.delay(ob_ids, status_value, request.user.user) # type: ignore

            return Response({
                'message': f'{updated_count} jobs updated successfully',
                'updated_count': updated_count
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsEmployerOrReadOnly, IsAdminOrReadOnly])
    def stats(self, request):
        """Get job statistics for employer"""
        if not request.user.is_employer() and not request.user.is_admin():
            return Response(
                {'error': 'Only employers, and admins can access this endpoint'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        queryset = self.get_queryset()
        
        stats = {
            'total_jobs': queryset.count(),
            'active_jobs': queryset.filter(status='published').count(),
            'featured_jobs': queryset.filter(is_featured=True).count(),
            'total_applications': JobApplication.objects.filter(job__in=queryset).count(),
            'total_views': sum(job.views_count for job in queryset),
        }
        
        # Calculate averages
        if stats['total_jobs'] > 0:
            stats['avg_applications_per_job'] = stats['total_applications'] / stats['total_jobs']
            stats['avg_views_per_job'] = stats['total_views'] / stats['total_jobs']
        else:
            stats['avg_applications_per_job'] = 0.0
            stats['avg_views_per_job'] = 0.0
        
        serializer = JobStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search jobs with advanced filters"""
        
        search_params = request.query_params
        search_engine = JobSearchEngine()
        results = search_engine.search(search_params)
        
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = JobResultSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = JobResultSerializer(results, many=True, context={'request': request})
        return Response(serializer.data)

class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationDetailSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = JobApplicationFilter
    filterset_fields = ['status', 'job__company']
    ordering_fields = ['applied_at', 'updated_at', 'score']
    ordering = ['-applied_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return JobApplication.objects.select_related('job', 'applicant').all()
        elif user.is_employer():
            return JobApplication.objects.select_related('job', 'applicant').filter(
                job__created_by=user
            )
        else:
            return JobApplication.objects.select_related('job').filter(
                applicant=user
            )
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return JobApplicationUpdateSerializer
        return JobApplicationDetailSerializer
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw job application"""
        application = self.get_object()
        
        if application.applicant != request.user:
            return Response(
                {'error': 'You can only withdraw your own applications'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if application.withdraw(request.user):
            return Response({'message': 'Application withdrawn successfully'})
        else:
            return Response(
                {'error': 'Application cannot be withdrawn'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        """Get user's job applications"""
        queryset = self.get_queryset().filter(applicant=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def for_my_jobs(self, request):
        """Get applications for user's job postings (employers only)"""
        if not request.user.is_employer():
            return Response(
                {'error': 'Only employers can access this endpoint'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SavedJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SavedJobSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['saved_at', 'job__published_at']
    ordering = ['-saved_at']
    
    def get_queryset(self):
        return SavedJob.objects.select_related('job__company', 'job__category').filter(
            user=self.request.user
        )
    
    @action(detail=True, methods=['delete'])
    def unsave(self, request, pk=None):
        """Remove job from saved jobs"""
        saved_job = self.get_object()
        saved_job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Clear all saved jobs"""
        deleted_count = self.get_queryset().delete()[0]
        return Response({
            'message': f'{deleted_count} saved jobs cleared',
            'deleted_count': deleted_count
        })