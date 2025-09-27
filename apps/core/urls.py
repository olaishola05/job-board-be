from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import JobCategoryViewSet, JobTypeViewSet, IndustryViewSet, SkillViewSet

core_router = DefaultRouter()

core_router.register('categories', JobCategoryViewSet, basename='category')
core_router.register('types', JobTypeViewSet, basename='type')
core_router.register('industries', IndustryViewSet, basename='industry')
core_router.register('skills', SkillViewSet, basename='skill')

app_name = 'core'

urlpatterns = [
    path('', include(core_router.urls)),
]