import re
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_email(to_email, template, context, subject, from_email=None):
    """
    Send email using template
    """
    try:
        html_content = render_to_string(template, context)
        
        send_mail(
            subject=subject,
            message='',
            html_message=html_content,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email] if isinstance(to_email, str) else to_email,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def geocode_address(address):
    """
    Geocode an address using a geocoding service
    Replace with actual implementation
    """
    # Mock implementation - integrate with Google Maps API, OpenCage, etc.
    return {
        'lat': 6.5244,  # Default to Lagos coordinates
        'lng': 3.3792,
        'formatted_address': address
    }


def validate_salary_range(salary_min, salary_max):
    """Validate that salary_min <= salary_max"""
    if salary_min and salary_max and salary_min > salary_max:
        raise ValidationError('Minimum salary cannot be greater than maximum salary')
      
      