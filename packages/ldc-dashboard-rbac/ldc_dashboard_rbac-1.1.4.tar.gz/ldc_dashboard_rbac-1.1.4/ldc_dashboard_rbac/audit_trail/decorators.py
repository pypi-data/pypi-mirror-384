"""
Decorators for automatic audit trail logging
"""
import functools
import asyncio
import inspect
from typing import Callable, Any, Dict, Optional, List
from django.http import HttpRequest
import logging

from .helpers import create_audit_log_helper
from .constants import AuditTrailActionTypes, AuditTrailEntityTypes
from .utils import extract_changes, get_trace_id 

logger = logging.getLogger(__name__)


def audit_trail(
    action_type: str,
    entity_type: str = None,
    entity_id_param: str = None,
    entity_id_attr: str = None,
    details_func: Callable = None,
    track_changes: bool = False,
    exclude_params: List[str] = None,
    include_response: bool = False,
    on_success_only: bool = False,
    async_logging: bool = False
):
    """
    Decorator for automatic audit trail logging
    
    Args:
        action_type: Type of action being performed
        entity_type: Type of entity being affected (optional, can be inferred)
        entity_id_param: Name of parameter containing entity ID
        entity_id_attr: Attribute path to extract entity ID from (e.g., 'user.id')
        details_func: Function to extract additional details
        track_changes: Whether to track before/after changes
        exclude_params: List of parameter names to exclude from details
        include_response: Whether to include response data in details
        on_success_only: Only log if operation is successful
        async_logging: Whether to log asynchronously (requires Celery)
    
    Usage:
        @audit_trail(
            action_type=AuditTrailActionTypes.UPDATE,
            entity_type=AuditTrailEntityTypes.USER,
            entity_id_param='user_id',
            track_changes=True
        )
        def update_user(request, user_id, **kwargs):
            # Your view logic here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request = None
            entity_id = None
            old_values = {}
            new_values = {}
            
            try:
                # Find request object
                for arg in args:
                    if isinstance(arg, HttpRequest):
                        request = arg
                        break
                
                if not request:
                    logger.warning(f"No request object found in {func.__name__}, skipping audit log")
                    return func(*args, **kwargs)
                
                # Extract entity ID
                entity_id = _extract_entity_id(
                    args, kwargs, entity_id_param, entity_id_attr
                )
                
                # Track changes if requested
                if track_changes and entity_id:
                    old_values = _get_entity_state(entity_type, entity_id)
                
                # Execute the original function
                result = func(*args, **kwargs)
                
                # Determine if operation was successful
                is_successful = True
                error_message = None
                
                if hasattr(result, 'status_code'):
                    is_successful = 200 <= result.status_code < 400
                    if not is_successful:
                        error_message = f"HTTP {result.status_code}"
                
                # Skip logging if on_success_only and operation failed
                if on_success_only and not is_successful:
                    return result
                
                # Track changes after operation
                if track_changes and entity_id and is_successful:
                    new_values = _get_entity_state(entity_type, entity_id)
                
                # Prepare details
                details = {}
                
                # Add function parameters to details (excluding sensitive ones)
                if not exclude_params:
                    exclude_params = ['password', 'token', 'secret', 'key']
                
                for key, value in kwargs.items():
                    if key not in exclude_params:
                        details[key] = str(value)[:500]  # Limit length
                
                # Add custom details if function provided
                if details_func:
                    try:
                        custom_details = details_func(*args, **kwargs)
                        if isinstance(custom_details, dict):
                            details.update(custom_details)
                    except Exception as e:
                        logger.warning(f"Error extracting custom details: {e}")
                
                # Add response details if requested
                if include_response and hasattr(result, 'data'):
                    details['response_data'] = str(result.data)[:1000]
                
                # Create audit log
                create_audit_log_helper(
                    request=request,
                    action_type=action_type,
                    entity_type=entity_type or 'unknown',
                    entity_id=entity_id or 0,
                    details=details,
                    old_values=old_values,
                    new_values=new_values,
                    is_successful=is_successful,
                    error_message=error_message
                )
                
                return result
                
            except Exception as e:
                # Log the exception but don't fail the original operation
                logger.error(f"Error in audit trail decorator for {func.__name__}: {e}")
                
                # Still try to create an audit log for the failure
                try:
                    create_audit_log_helper(
                        request=request,
                        action_type=action_type,
                        entity_type=entity_type or 'unknown',
                        entity_id=entity_id or 0,
                        details={'error': str(e)},
                        is_successful=False,
                        error_message=str(e)
                    )
                except:
                    pass  # Don't let audit logging break the main operation
                
                # Re-raise the original exception
                raise
        
        return wrapper
    return decorator


def audit_trail_async(
    action_type: str,
    entity_type: str = None,
    entity_id_param: str = None,
    entity_id_attr: str = None,
    details_func: Callable = None,
    track_changes: bool = False,
    exclude_params: List[str] = None,
    include_response: bool = False,
    on_success_only: bool = False
):
    """
    Async version of audit_trail decorator for async views
    
    Usage:
        @audit_trail_async(
            action_type=AuditTrailActionTypes.CREATE,
            entity_type=AuditTrailEntityTypes.USER,
            entity_id_attr='result.id'
        )
        async def create_user_async(request, **kwargs):
            # Your async view logic here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            entity_id = None
            old_values = {}
            new_values = {}
            
            try:
                # Find request object
                for arg in args:
                    if isinstance(arg, HttpRequest):
                        request = arg
                        break
                
                if not request:
                    logger.warning(f"No request object found in {func.__name__}, skipping audit log")
                    return await func(*args, **kwargs)
                
                # Extract entity ID
                entity_id = _extract_entity_id(
                    args, kwargs, entity_id_param, entity_id_attr
                )
                
                # Track changes if requested
                if track_changes and entity_id:
                    old_values = _get_entity_state(entity_type, entity_id)
                
                # Execute the original function
                result = await func(*args, **kwargs)
                
                # Determine if operation was successful
                is_successful = True
                error_message = None
                
                if hasattr(result, 'status_code'):
                    is_successful = 200 <= result.status_code < 400
                    if not is_successful:
                        error_message = f"HTTP {result.status_code}"
                
                # Skip logging if on_success_only and operation failed
                if on_success_only and not is_successful:
                    return result
                
                # Track changes after operation
                if track_changes and entity_id and is_successful:
                    new_values = _get_entity_state(entity_type, entity_id)
                
                # Prepare details
                details = {}
                
                # Add function parameters to details (excluding sensitive ones)
                if not exclude_params:
                    exclude_params = ['password', 'token', 'secret', 'key']
                
                for key, value in kwargs.items():
                    if key not in exclude_params:
                        details[key] = str(value)[:500]  # Limit length
                
                # Add custom details if function provided
                if details_func:
                    try:
                        if asyncio.iscoroutinefunction(details_func):
                            custom_details = await details_func(*args, **kwargs)
                        else:
                            custom_details = details_func(*args, **kwargs)
                        if isinstance(custom_details, dict):
                            details.update(custom_details)
                    except Exception as e:
                        logger.warning(f"Error extracting custom details: {e}")
                
                # Add response details if requested
                if include_response and hasattr(result, 'data'):
                    details['response_data'] = str(result.data)[:1000]
                
                # Create audit log
                create_audit_log_helper(
                    request=request,
                    action_type=action_type,
                    entity_type=entity_type or 'unknown',
                    entity_id=entity_id or 0,
                    details=details,
                    old_values=old_values,
                    new_values=new_values,
                    is_successful=is_successful,
                    error_message=error_message
                )
                
                return result
                
            except Exception as e:
                # Log the exception but don't fail the original operation
                logger.error(f"Error in async audit trail decorator for {func.__name__}: {e}")
                
                # Still try to create an audit log for the failure
                try:
                    create_audit_log_helper(
                        request=request,
                        action_type=action_type,
                        entity_type=entity_type or 'unknown',
                        entity_id=entity_id or 0,
                        details={'error': str(e)},
                        is_successful=False,
                        error_message=str(e)
                    )
                except:
                    pass  # Don't let audit logging break the main operation
                
                # Re-raise the original exception
                raise
        
        return wrapper
    return decorator


def _extract_entity_id(args, kwargs, entity_id_param, entity_id_attr):
    """Extract entity ID from function parameters or attributes"""
    entity_id = None
    
    # Try to get from parameter
    if entity_id_param and entity_id_param in kwargs:
        entity_id = kwargs[entity_id_param]
    
    # Try to get from attribute path
    if not entity_id and entity_id_attr:
        try:
            # Handle dot notation like 'user.id' or 'result.user.id'
            obj = None
            if entity_id_attr.startswith('result.'):
                # This would need the result, which we don't have yet
                # This is handled in a post-execution phase
                pass
            else:
                # Look in kwargs first
                attr_parts = entity_id_attr.split('.')
                if attr_parts[0] in kwargs:
                    obj = kwargs[attr_parts[0]]
                    for part in attr_parts[1:]:
                        obj = getattr(obj, part, None)
                        if obj is None:
                            break
                    entity_id = obj
        except Exception as e:
            logger.warning(f"Error extracting entity ID from attribute {entity_id_attr}: {e}")
    
    return entity_id


def _get_entity_state(entity_type, entity_id):
    """Get current state of an entity for change tracking"""
    try:
        # This is a placeholder - implement based on your entity types
        # You might want to use Django's ContentType framework here
        from django.apps import apps
        
        # Map entity types to models (this should be configurable)
        entity_model_map = {
            AuditTrailEntityTypes.USER: 'auth.User',
            AuditTrailEntityTypes.DASHBOARD_USER: 'dashboard.DashboardUser',
            # Add more mappings as needed
        }
        
        if entity_type in entity_model_map:
            model_path = entity_model_map[entity_type]
            app_label, model_name = model_path.split('.')
            model_class = apps.get_model(app_label, model_name)
            
            try:
                instance = model_class.objects.get(pk=entity_id)
                # Extract relevant fields (exclude sensitive ones)
                state = {}
                for field in instance._meta.fields:
                    if not field.name.endswith('password') and not field.name.endswith('token'):
                        value = getattr(instance, field.name)
                        if value is not None:
                            state[field.name] = str(value)
                return state
            except model_class.DoesNotExist:
                return {}
        
        return {}
    except Exception as e:
        logger.warning(f"Error getting entity state for {entity_type}({entity_id}): {e}")
        return {}
