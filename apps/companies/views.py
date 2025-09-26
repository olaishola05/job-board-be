from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from .models import Company, CompanyReview, CompanyAnalytics
from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer, CompanyCreateUpdateSerializer, CompanyReviewSerializer, CompanyReviewCreateSerializer,
    CompanyAnalyticsSerializer,
    CompanyStatsSerializer
)
from apps.core.permissions import IsOwnerOrReadOnly
from apps.accounts.permissions import (
    IsEmployerOrAdmin, IsCompanyOwnerOrAdmin, IsAdminUser
)
from apps.core.pagination import StandardPagination
from .filters import CompanyFilter
from .tasks import send_company_approved_email, notify_company_rejection, notify_company_creation

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.select_related('industry', 'created_by').prefetch_related('media')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = StandardPagination
    filterset_class = CompanyFilter
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'created_at', 'rating', 'follower_count', 'job_count']
    ordering = ['-is_featured', '-created_at']
    
    def get_serializer_class(self): # type: ignore
        if self.action == 'list':
            return CompanyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CompanyCreateUpdateSerializer
        return CompanyDetailSerializer
      
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), IsEmployerOrAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsCompanyOwnerOrAdmin()]
        elif self.action in ['analytics', 'approve', 'reject']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self): # type: ignore
        user = self.request.user
        queryset = self.queryset.annotate(
            active_job_count=Count('jobs', filter=Q(jobs__status='published')),
            total_followers=Count('followers')
        )
        
        if self.action == 'list':
            # Filter based on user role
            if not user.is_authenticated or user.role != 'admin':
                queryset = queryset.filter(is_active=True, approval_status='approved')
        
        return queryset

    def perform_create(self, serializer):
        company = serializer.save(created_by=self.request.user)
        # Auto-approve for admin users
        if self.request.user.role == 'admin':
            company.approval_status = 'approved'
            company.is_verified = True
            company.approved_at = timezone.now()
            company.save()
            notify_company_creation.delay(company.id)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Company.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsCompanyOwnerOrAdmin])
    def analytics(self, request, pk=None):
        company = self.get_object()
        analytics, _ = CompanyAnalytics.objects.get_or_create(company=company)
        serializer = CompanyAnalyticsSerializer(analytics)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        cache_key = 'company_stats'
        stats = cache.get(cache_key)
        
        if not stats:
            last_month = timezone.now() - timedelta(days=30)
            
            total_companies = Company.objects.count()
            verified_companies = Company.objects.filter(is_verified=True).count()
            featured_companies = Company.objects.filter(is_featured=True).count()
            
            # Corrected annotation to avoid conflict with model field
            companies_with_jobs = Company.objects.annotate(
                published_jobs_count=Count('jobs', filter=Q(jobs__status='published'))
            ).filter(published_jobs_count__gt=0).count()
            
            # Top industries
            top_industries = Company.objects.values('industry__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            # Average rating
            avg_rating = Company.objects.aggregate(
                avg=Avg('rating', filter=Q(rating__isnull=False))
            )['avg'] or 0
            
            # Monthly growth
            current_month = Company.objects.filter(created_at__gte=last_month).count()
            previous_month = Company.objects.filter(
                created_at__gte=last_month - timedelta(days=30),
                created_at__lt=last_month
            ).count()
            growth = ((current_month - previous_month) / max(previous_month, 1)) * 100
            
            stats = {
                'total_companies': total_companies,
                'verified_companies': verified_companies,
                'featured_companies': featured_companies,
                'companies_with_jobs': companies_with_jobs,
                'top_industries': list(top_industries),
                'avg_company_rating': round(avg_rating, 2),
                'monthly_growth': round(growth, 2)
            }
            cache.set(cache_key, stats, 3600)
        
        serializer = CompanyStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def approve(self, request, pk=None):
        company = self.get_object()
        company.approval_status = 'approved'
        company.is_verified = True
        company.approved_at = timezone.now()
        company.save()
        send_company_approved_email.delay(company.id)
        return Response({'message': 'Company approved successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def reject(self, request, pk=None):
        company = self.get_object()
        company.approval_status = 'rejected'
        company.is_verified = False
        company.save()
        notify_company_rejection.delay(company.id, "Your company did not meet our verification criteria.")
        return Response({'message': 'Company rejected'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def feature(self, request, pk=None):
        company = self.get_object()
        company.is_featured = not company.is_featured
        company.save()
        message = 'Company featured' if company.is_featured else 'Company unfeatured'
        return Response({'message': message})

    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        company = self.get_object()
        from apps.jobs.models import Job
        from apps.jobs.serializers import JobListSerializer
        
        jobs = Job.published.filter(company=company).order_by('-published_at')
        page = self.paginate_queryset(jobs)
        serializer = JobListSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    def _update_company_rating(self, company):
        """Update company's average rating based on reviews"""
        rating_data = company.reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        company.rating = rating_data['avg_rating']
        company.review_count = rating_data['count']
        company.save(update_fields=['rating', 'review_count'])
