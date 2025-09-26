# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import (
#     JobViewSet, JobApplicationViewSet, SavedJobViewSet, JobAlertViewSet,
#     JobCategoryViewSet, JobTypeViewSet, IndustryViewSet, SkillViewSet
# )

# router = DefaultRouter()
# router.register(r'', JobViewSet, basename='job')
# router.register(r'applications', JobApplicationViewSet, basename='jobapplication')
# router.register(r'saved-jobs', SavedJobViewSet, basename='savedjob')
# router.register(r'alerts', JobAlertViewSet, basename='jobalert')
# router.register(r'categories', JobCategoryViewSet, basename='jobcategory')
# router.register(r'types', JobTypeViewSet, basename='jobtype')
# router.register(r'industries', IndustryViewSet, basename='industry')
# router.register(r'skills', SkillViewSet, basename='skill')

# app_name = 'jobs'

# urlpatterns = [
#     path('', include(router.urls)),
# ]

# jobs/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobViewSet, JobApplicationViewSet, SavedJobViewSet,
)

jobs_router = DefaultRouter()
jobs_router.register(r'', JobViewSet, basename='job')
jobs_router.register(r'applications', JobApplicationViewSet, basename='jobapplication')
jobs_router.register(r'saved-jobs', SavedJobViewSet, basename='savedjob')

app_name = 'jobs'

urlpatterns = [
    path('', include(jobs_router.urls)),
]
