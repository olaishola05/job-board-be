import logging
import time
from django.utils.deprecation import MiddlewareMixin
from ipware import get_client_ip

logger = logging.getLogger(__name__)

class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests and responses
    """
    def process_request(self, request):
        request.start_time = time.time()
        
        if request.path.startswith('/api/'):
            logger.info(
                f"API Request: {request.method} {request.path}",
                extra={
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    'ip': get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')
                }
            )
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time') and request.path.startswith('/api/'):
            duration = time.time() - request.start_time
            logger.info(
                f"API Response: {request.method} {request.path} - {response.status_code} ({duration:.3f}s)",
                extra={
                    'status_code': response.status_code,
                    'duration': duration
                }
            )
        
        return response
