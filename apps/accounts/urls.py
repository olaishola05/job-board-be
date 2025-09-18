from django.urls import path, include
from rest_framework import routers
from .views import UserRegistrationViewSet, UserViewSet, ProfileViewSet, LoginViewSet, PasswordResetViewSet, LogoutViewSet, ResendVerificationViewSet, TokenRefreshViewSet, EmailVerificationViewSet, PasswordChangeViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'auth/register', UserRegistrationViewSet, basename='registration')
router.register(r'auth/login', LoginViewSet, basename='login')
router.register(r'auth/password-reset', PasswordResetViewSet, basename='password-reset')
router.register(r'auth/logout', LogoutViewSet, basename='logout')
router.register(r'auth/resend-verification', ResendVerificationViewSet, basename='resend-verification')
router.register(r'auth/token/refresh', TokenRefreshViewSet, basename='token-refresh')
router.register(r'auth/verify-email', EmailVerificationViewSet, basename='email-verify')
router.register(r'auth/password-change', PasswordChangeViewSet, basename='password-change')

app_name = 'Accounts'

urlpatterns = [
    path('', include(router.urls)),  
]