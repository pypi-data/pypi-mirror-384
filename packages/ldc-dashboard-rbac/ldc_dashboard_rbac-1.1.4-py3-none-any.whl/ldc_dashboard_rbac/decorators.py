"""
Decorators for simplified RBAC system
"""
from functools import wraps
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
import logging

from ldc_dashboard_rbac.constants import (
    SettingsKeys, ErrorMessages, TemplatePaths, HTTPStatus, APIDetection
)
from ldc_dashboard_rbac.permissions import (
    get_rbac_config, user_has_feature_permission, is_superadmin_user, is_admin_user
)

logger = logging.getLogger(__name__)


def _is_api_request(request) -> bool:
    """Check if request is an API request"""
    # Check AJAX header
    if request.headers.get(APIDetection.AJAX_HEADER) == APIDetection.AJAX_VALUE:
        return True
    
    # Check content type
    content_type = request.headers.get('Content-Type', '').lower()
    if any(ct in content_type for ct in [APIDetection.JSON_CONTENT_TYPE, APIDetection.API_JSON_CONTENT_TYPE]):
        return True
    
    # Check user agent
    user_agent = request.headers.get('User-Agent', '').lower()
    if any(ua in user_agent for ua in APIDetection.API_USER_AGENTS):
        return True
    
    # Check URL pattern
    if APIDetection.API_URL_PATTERN in request.path:
        return True
    
    return False


def _handle_permission_denied(request, error_message: str, feature_name: str = None):
    """Handle permission denied response"""
    if _is_api_request(request):
        return JsonResponse({
            'error': error_message,
            'feature': feature_name,
            'status': 'permission_denied'
        }, status=HTTPStatus.FORBIDDEN)
    else:
        # Render HTML template
        context = {
            'error_message': error_message,
            'feature_name': feature_name,
            'site_url': getattr(settings, SettingsKeys.SITE_URL, ''),
        }
        
        html_content = render_to_string(TemplatePaths.PERMISSION_DENIED, context)
        return HttpResponse(html_content, status=HTTPStatus.FORBIDDEN)


def feature_required(feature_url_name: str):
    """
    Decorator to check if user has access to a feature - Simplified Version
    Only checks if user has access to the feature through group membership
    
    Usage:
        @feature_required('vendor_management')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                # Get user using configured getter
                config = get_rbac_config()
                user_getter = config.get(SettingsKeys.GroupRBAC.USER_GETTER)
                
                if not user_getter or not callable(user_getter):
                    logger.error("USER_GETTER not configured or not callable")
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.USER_GETTER_NOT_CONFIGURED,
                        feature_url_name
                    )
                
                user = user_getter(request)
                
                if not user:
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.NO_FEATURE_PERMISSION,
                        feature_url_name
                    )
                
                # Check if user has permission - Simplified
                if not user_has_feature_permission(user, feature_url_name):
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.NO_FEATURE_PERMISSION,
                        feature_url_name
                    )
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in feature_required decorator: {e}")
                return _handle_permission_denied(
                    request,
                    ErrorMessages.NO_FEATURE_PERMISSION,
                    feature_url_name
                )
        
        return _wrapped_view
    return decorator


def admin_required(view_func=None):
    """
    Decorator to check if user is admin or superadmin - Simplified Version
    
    Usage:
        @admin_required
        def my_admin_view(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                # Get user using configured getter
                config = get_rbac_config()
                user_getter = config.get(SettingsKeys.GroupRBAC.USER_GETTER)
                
                if not user_getter or not callable(user_getter):
                    logger.error("USER_GETTER not configured or not callable")
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.USER_GETTER_NOT_CONFIGURED
                    )
                
                user = user_getter(request)
                
                if not user:
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.NO_ADMIN_PERMISSION
                    )
                
                # Check if user is admin or superadmin
                if not (is_admin_user(user) or is_superadmin_user(user)):
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.NO_ADMIN_PERMISSION
                    )
                
                return func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in admin_required decorator: {e}")
                return _handle_permission_denied(
                    request,
                    ErrorMessages.NO_ADMIN_PERMISSION
                )
        
        return _wrapped_view
    
    if view_func:
        return decorator(view_func)
    return decorator


def superadmin_required(view_func=None):
    """
    Decorator to check if user is superadmin - Simplified Version
    
    Usage:
        @superadmin_required
        def my_superadmin_view(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                # Get user using configured getter
                config = get_rbac_config()
                user_getter = config.get(SettingsKeys.GroupRBAC.USER_GETTER)
                
                if not user_getter or not callable(user_getter):
                    logger.error("USER_GETTER not configured or not callable")
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.USER_GETTER_NOT_CONFIGURED
                    )
                
                user = user_getter(request)
                
                if not user:
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.NO_SUPERADMIN_PERMISSION
                    )
                
                # Check if user is superadmin
                if not is_superadmin_user(user):
                    return _handle_permission_denied(
                        request,
                        ErrorMessages.NO_SUPERADMIN_PERMISSION
                    )
                
                return func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in superadmin_required decorator: {e}")
                return _handle_permission_denied(
                    request,
                    ErrorMessages.NO_SUPERADMIN_PERMISSION
                )
        
        return _wrapped_view
    
    if view_func:
        return decorator(view_func)
    return decorator