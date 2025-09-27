from urllib import request
from django.shortcuts import render
from apps import jobs
from apps.jobs.serializers import JobCategorySerializer, JobListSerializer, JobTypeSerializer, IndustrySerializer, SkillSerializer
from apps.jobs.models import JobCategory, Job, JobType, Industry, Skill
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status, filters

# Create your views here.
class JobCategoryViewSet(viewsets.ModelViewSet):
    queryset = JobCategory.active.all()
    serializer_class = JobCategorySerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['sort_order', 'name']
    http_method_names = ['get', 'post', 'patch', 'delete',]
    
    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """Get jobs in this category"""
        category = self.get_object()
        jobs = Job.published.filter(category=category)
        
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = JobListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = JobListSerializer(jobs, many=True, context={'request': request})
        return Response(serializer.data)

class JobTypeViewSet(viewsets.ModelViewSet):
    queryset = JobType.active.all()
    serializer_class = JobTypeSerializer
    ordering = ['sort_order', 'name']
    http_method_names = ['get', 'post', 'patch', 'delete',]

class IndustryViewSet(viewsets.ModelViewSet):
    queryset = Industry.active.all()
    serializer_class = IndustrySerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['sort_order', 'name']
    http_method_names = ['get', 'post', 'patch', 'delete',]

    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """Get jobs in this industry"""
        industry = self.get_object()
        jobs = Job.published.filter(industry=industry)
        
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = JobListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = JobListSerializer(jobs, many=True, context={'request': request})
        return Response(serializer.data)

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.active.all()
    serializer_class = SkillSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['-popularity_score', 'name']
    http_method_names = ['get', 'post', 'patch', 'delete',]
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular skills"""
        popular_skills = self.get_queryset().order_by('-popularity_score')[:20]
        serializer = self.get_serializer(popular_skills, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        """Get jobs for a skill"""
        skill = self.get_object()
        jobs = Job.published.filter(skills=skill)
        
        page = self.paginate_queryset(jobs)
        if page is not None:
          serializer = JobListSerializer(page, many=True, context={'request': request})
          return self.get_paginated_response(serializer.data)
        
        serializer = JobListSerializer(jobs, many=True, context={'request': request})
        return Response(serializer.data)
