"""
Job Board Platform URL Configuration
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

schema_view = get_schema_view(
    openapi.Info(
        title="Job Board Platform API",
        default_version='v1',
        description="A comprehensive job board platform with advanced features",
        terms_of_service="https://www.jobboard.com/terms/",
        contact=openapi.Contact(email="api@jobboard.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path(f'{settings.ADMIN_URL}', admin.site.urls),
    
    path('health/', include('health_check.urls')),
    
    # API Documentation
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # API v1
    path('api/v1/', include([
        path('accounts/', include('apps.accounts.urls')),
        path('jobs/', include('apps.jobs.urls')),
        path('core/', include('apps.core.urls')),
        path('companies/', include('apps.companies.urls')),
    ])),
    
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),
]

# Development URLs
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Job Board Platform Administration"
admin.site.site_title = "Job Board Platform Admin"
admin.site.index_title = "Welcome to Job Board Platform Administration"