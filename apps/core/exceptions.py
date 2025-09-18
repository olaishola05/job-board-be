from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

def custom_exception_handler(exc, context):
    """Custom exception handler"""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status': response.status_code
        }
        
        # Handle specific exception types
        if isinstance(exc, Http404):
            custom_response_data['message'] = 'Resource not found'
        elif isinstance(exc, DjangoValidationError):
            custom_response_data['message'] = 'Validation error'
            custom_response_data['details'] = exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
        
        response.data = custom_response_data
    
    return response