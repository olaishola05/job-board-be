from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from datetime import timedelta

from .models import Company, CompanyReview, CompanyAnalytics
from .serializers import (
    CompanyListSerializer, CompanyDetailSerializer, CompanyCreateUpdateSerializer, CompanyReviewSerializer, CompanyReviewCreateSerializer,
    CompanyAnalyticsSerializer, CompanySearchSerializer,
    CompanyStatsSerializer
)
from apps.core.permissions import IsOwnerOrReadOnly
from apps.accounts.permissions import (
    IsEmployerOrAdmin, IsCompanyOwnerOrAdmin, IsAdminUser
)

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.select_related('industry', 'created_by').prefetch_related('media')

    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CompanyCreateUpdateSerializer
        return CompanyDetailSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), IsEmployerOrAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsCompanyOwnerOrAdmin()]
        elif self.action in ['analytics', 'approve', 'reject']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Company.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        company = self.get_object()
        
        if request.method == 'GET':
            reviews = company.reviews.select_related('user').order_by('-created_at')
            page = self.paginate_queryset(reviews)
            serializer = CompanyReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        elif request.method == 'POST':
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
            
            if CompanyReview.objects.filter(company=company, user=request.user).exists():
                return Response({'error': 'You have already reviewed this company'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            serializer = CompanyReviewCreateSerializer(data=request.data)
            if serializer.is_valid():
                review = serializer.save(company=company, user=request.user)
                
                self._update_company_rating(company)
                
                response_serializer = CompanyReviewSerializer(
                    review, context={'request': request}
                )
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsCompanyOwnerOrAdmin])
    def analytics(self, request, pk=None):
        company = self.get_object()
        analytics, _ = CompanyAnalytics.objects.get_or_create(company=company)
        serializer = CompanyAnalyticsSerializer(analytics)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        serializer = CompanySearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset()
        
        # Apply filters
        if data.get('q'):
            queryset = queryset.filter(
                Q(name__icontains=data['q']) |
                Q(description__icontains=data['q']) |
                Q(location__icontains=data['q'])
            )
        
        if data.get('industry'):
            queryset = queryset.filter(industry_id=data['industry'])
        
        if data.get('location'):
            queryset = queryset.filter(location__icontains=data['location'])
        
        if data.get('company_size'):
            queryset = queryset.filter(company_size=data['company_size'])
        
        if data.get('is_verified') is not None:
            queryset = queryset.filter(is_verified=data['is_verified'])
        
        if data.get('is_featured') is not None:
            queryset = queryset.filter(is_featured=data['is_featured'])
        
        if data.get('min_rating'):
            queryset = queryset.filter(rating__gte=data['min_rating'])
        
        if data.get('founded_year_min'):
            queryset = queryset.filter(founded_year__gte=data['founded_year_min'])
        
        if data.get('founded_year_max'):
            queryset = queryset.filter(founded_year__lte=data['founded_year_max'])
        
        # Apply ordering
        ordering = data.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        serializer = CompanyListSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        cache_key = 'company_stats'
        stats = cache.get(cache_key)
        
        if not stats:
            last_month = timezone.now() - timedelta(days=30)
            
            total_companies = Company.objects.count()
            verified_companies = Company.objects.filter(is_verified=True).count()
            featured_companies = Company.objects.filter(is_featured=True).count()
            companies_with_jobs = Company.objects.annotate(
                job_count=Count('jobs', filter=Q(jobs__status='published'))
            ).filter(job_count__gt=0).count()
            
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
        return Response({'message': 'Company approved successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def reject(self, request, pk=None):
        company = self.get_object()
        company.approval_status = 'rejected'
        company.is_verified = False
        company.save()
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