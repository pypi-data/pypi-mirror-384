"""
Middleware for automatic audit trail logging
"""
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.urls import resolve
import logging

from .helpers import create_audit_log_helper
from .constants import AuditTrailActionTypes, AuditTrailEntityTypes
from .utils import get_client_ip, get_user_agent, get_trace_id

logger = logging.getLogger(__name__)


class AuditTrailMiddleware(MiddlewareMixin):
    """
    Middleware for automatic audit trail logging
    
    This middleware can automatically log certain requests based on configuration.
    It's useful for tracking page views, API calls, and other HTTP interactions.
    
    Configuration in settings.py:
    
    AUDIT_TRAIL_CONFIG = {
        'MIDDLEWARE_ENABLED': True,
        'LOG_ALL_REQUESTS': False,
        'LOG_AUTHENTICATED_ONLY': True,
        'INCLUDE_PATHS': ['/api/', '/admin/'],
        'EXCLUDE_PATHS': ['/static/', '/media/', '/health/'],
        'LOG_GET_REQUESTS': False,
        'LOG_POST_REQUESTS': True,
        'LOG_PUT_REQUESTS': True,
        'LOG_DELETE_REQUESTS': True,
        'LOG_RESPONSE_DATA': False,
        'MAX_RESPONSE_SIZE': 1000,
    }
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.config = getattr(settings, 'AUDIT_TRAIL_CONFIG', {})
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming request"""
        # Store start time for performance tracking
        request._audit_start_time = time.time()
        
        # Store trace ID
        request.trace_id = get_trace_id(request)
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response"""
        try:
            # Check if middleware is enabled
            if not self.config.get('MIDDLEWARE_ENABLED', False):
                return response
            
            # Check if we should log this request
            if not self._should_log_request(request, response):
                return response
            
            # Calculate execution time
            execution_time = None
            if hasattr(request, '_audit_start_time'):
                execution_time = time.time() - request._audit_start_time
            
            # Determine action type based on HTTP method
            action_type = self._get_action_type(request.method)
            
            # Extract entity information from URL
            entity_type, entity_id = self._extract_entity_info(request)
            
            # Prepare audit details
            details = {
                'request_path': request.path,
                'request_method': request.method,
                'response_status': response.status_code,
                'execution_time': execution_time,
                'query_params': dict(request.GET) if request.GET else {},
            }
            
            # Add POST data if configured and safe
            if (request.method in ['POST', 'PUT', 'PATCH'] and 
                self.config.get('LOG_REQUEST_DATA', False)):
                try:
                    if hasattr(request, 'body') and request.body:
                        # Only log if content type is JSON
                        content_type = request.META.get('CONTENT_TYPE', '')
                        if 'application/json' in content_type:
                            body_data = json.loads(request.body.decode('utf-8'))
                            # Remove sensitive fields
                            details['request_data'] = self._sanitize_data(body_data)
                except Exception:
                    pass  # Skip if can't parse
            
            # Add response data if configured
            if (self.config.get('LOG_RESPONSE_DATA', False) and 
                hasattr(response, 'content')):
                try:
                    max_size = self.config.get('MAX_RESPONSE_SIZE', 1000)
                    if len(response.content) <= max_size:
                        details['response_data'] = response.content.decode('utf-8')[:max_size]
                except Exception:
                    pass  # Skip if can't decode
            
            # Create audit log
            create_audit_log_helper(
                request=request,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id or 0,
                details=details,
                is_successful=200 <= response.status_code < 400
            )
            
        except Exception as e:
            logger.error(f"Error in AuditTrailMiddleware: {e}")
        
        return response
    
    def _should_log_request(self, request, response):
        """Determine if request should be logged"""
        # Check if user is authenticated (if required)
        if self.config.get('LOG_AUTHENTICATED_ONLY', True):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return False
        
        # Check HTTP method
        method_config_map = {
            'GET': 'LOG_GET_REQUESTS',
            'POST': 'LOG_POST_REQUESTS',
            'PUT': 'LOG_PUT_REQUESTS',
            'PATCH': 'LOG_PUT_REQUESTS',
            'DELETE': 'LOG_DELETE_REQUESTS',
        }
        
        method_config = method_config_map.get(request.method)
        if method_config and not self.config.get(method_config, True):
            return False
        
        # Check path inclusion/exclusion
        path = request.path
        
        # Check exclude paths
        exclude_paths = self.config.get('EXCLUDE_PATHS', [])
        for exclude_path in exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # Check include paths (if specified)
        include_paths = self.config.get('INCLUDE_PATHS', [])
        if include_paths:
            for include_path in include_paths:
                if path.startswith(include_path):
                    return True
            return False  # Path not in include list
        
        # Log all requests if no specific paths configured
        return self.config.get('LOG_ALL_REQUESTS', False)
    
    def _get_action_type(self, method):
        """Map HTTP method to audit action type"""
        method_map = {
            'GET': AuditTrailActionTypes.VIEW,
            'POST': AuditTrailActionTypes.CREATE,
            'PUT': AuditTrailActionTypes.UPDATE,
            'PATCH': AuditTrailActionTypes.UPDATE,
            'DELETE': AuditTrailActionTypes.DELETE,
        }
        return method_map.get(method, AuditTrailActionTypes.ACCESS)
    
    def _extract_entity_info(self, request):
        """Extract entity type and ID from URL"""
        try:
            # Try to resolve the URL to get view information
            resolver_match = resolve(request.path)
            view_name = resolver_match.view_name
            
            # Extract entity type from URL pattern
            entity_type = 'unknown'
            entity_id = None
            
            # Look for common patterns in URL
            path_parts = request.path.strip('/').split('/')
            
            # Try to find ID in URL
            for part in path_parts:
                if part.isdigit():
                    entity_id = int(part)
                    break
            
            # Try to determine entity type from URL
            if 'user' in request.path.lower():
                entity_type = AuditTrailEntityTypes.USER
            elif 'group' in request.path.lower():
                entity_type = AuditTrailEntityTypes.GROUP
            elif 'feature' in request.path.lower():
                entity_type = AuditTrailEntityTypes.FEATURE
            elif 'api' in request.path.lower():
                entity_type = 'api_endpoint'
            else:
                # Use the first non-numeric path part
                for part in path_parts:
                    if part and not part.isdigit():
                        entity_type = part
                        break
            
            return entity_type, entity_id
            
        except Exception as e:
            logger.warning(f"Error extracting entity info from URL {request.path}: {e}")
            return 'unknown', None
    
    def _sanitize_data(self, data):
        """Remove sensitive information from data"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = ['password', 'token', 'secret', 'key', 'credential']
        sanitized = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
