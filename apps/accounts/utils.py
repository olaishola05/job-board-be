
from django.core.validators import RegexValidator
from ipware import get_client_ip
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from django.utils import timezone
import re
from django.core.exceptions import ValidationError

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

def get_req_ip(request):
    """Get client IP address"""
    ip_address, _ = get_client_ip(request)
    
    if ip_address is None:
      ip_address = '0.0.0.0'
      
    return ip_address

def create_jwt_tokens(user, request):
    """Create JWT access and refresh tokens"""
    from .models import RefreshToken

    refresh = JWTRefreshToken.for_user(user)
    refresh_token = RefreshToken.create_token(
        user=user,
        device_info=request.META.get('HTTP_USER_AGENT', ''),
        ip_address=get_req_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return {
        'access': str(refresh.access_token),
        'refresh': refresh_token.token,
        'access_token_expiry': timezone.now() + timezone.timedelta(minutes=15),
        'refresh_token_expiry': refresh_token.expires_at
    }
    
def log_login_attempt(email, request, success=True, failure_reason=None):
    """Log login attempt for security monitoring"""
    
    from .models import LoginAttempt
    
    LoginAttempt.objects.create(
        email=email,
        ip_address=get_req_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        success=success,
        failure_reason=failure_reason
    )
    
def validate_linkedin_url(value):
    """Validate LinkedIn URL format"""
    linkedin_regex = re.compile(r'^https?://(www\.)?linkedin\.com/in/[\w-]+/?$')
    if not linkedin_regex.match(value):
        raise ValidationError('Invalid LinkedIn URL format')


def validate_github_url(value):
    """Validate GitHub URL format"""
    github_regex = re.compile(r'^https?://(www\.)?github\.com/[\w-]+/?$')
    if not github_regex.match(value):
        raise ValidationError('Invalid GitHub URL format')
    