"""
Utility functions for audit trail functionality
"""
import json
import uuid
from typing import Dict, Any, Optional, List
from django.http import HttpRequest
from django.conf import settings
import logging

from .constants import AuditTrailConstants

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """
    Extract client IP address from request
    
    Args:
        request: Django request object
    
    Returns:
        Client IP address or None
    """
    try:
        # Check for forwarded IP first (load balancer/proxy)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        
        # Check for real IP (some proxies use this)
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip.strip()
        
        # Fall back to remote address
        remote_addr = request.META.get('REMOTE_ADDR')
        if remote_addr:
            return remote_addr.strip()
        
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting client IP: {e}")
        return None


def get_user_agent(request: HttpRequest) -> Optional[str]:
    """
    Extract user agent from request
    
    Args:
        request: Django request object
    
    Returns:
        User agent string or None
    """
    try:
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent:
            # Limit length to prevent database issues
            return user_agent[:1000]
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting user agent: {e}")
        return None


def get_trace_id(request: HttpRequest) -> Optional[str]:
    """
    Extract or generate trace ID for request tracking
    
    Args:
        request: Django request object
    
    Returns:
        Trace ID string
    """
    try:
        # Check if trace ID is already set in request
        if hasattr(request, 'trace_id'):
            return request.trace_id
        
        # Check for trace ID in headers
        trace_id = request.META.get('HTTP_X_TRACE_ID')
        if trace_id:
            return trace_id[:100]  # Limit length
        
        # Check for request ID in headers (common in some setups)
        request_id = request.META.get('HTTP_X_REQUEST_ID')
        if request_id:
            return request_id[:100]
        
        # Generate a new trace ID
        trace_id = str(uuid.uuid4())[:32]  # Use first 32 chars of UUID
        
        # Store it in request for reuse
        request.trace_id = trace_id
        
        return trace_id
        
    except Exception as e:
        logger.warning(f"Error getting trace ID: {e}")
        return str(uuid.uuid4())[:32]


def sanitize_audit_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize audit data by removing or masking sensitive information
    
    Args:
        data: Dictionary containing audit data
    
    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data
    
    # Get sensitive fields from configuration
    config = getattr(settings, 'AUDIT_TRAIL_CONFIG', {})
    sensitive_fields = config.get('SENSITIVE_FIELDS', AuditTrailConstants.SENSITIVE_FIELDS)
    
    sanitized_data = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if field is sensitive
        is_sensitive = any(sensitive_field in key_lower for sensitive_field in sensitive_fields)
        
        if is_sensitive:
            if value:
                sanitized_data[key] = '[REDACTED]'
            else:
                sanitized_data[key] = value
        else:
            # Recursively sanitize nested dictionaries
            if isinstance(value, dict):
                sanitized_data[key] = sanitize_audit_data(value)
            elif isinstance(value, list):
                sanitized_data[key] = [
                    sanitize_audit_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # Convert to string and limit length
                sanitized_data[key] = str(value)[:1000] if value is not None else value
    
    return sanitized_data


def extract_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract changes between old and new data
    
    Args:
        old_data: Previous data state
        new_data: New data state
    
    Returns:
        Dictionary containing change information
    """
    if not isinstance(old_data, dict) or not isinstance(new_data, dict):
        return {}
    
    changes = {
        'added': {},
        'modified': {},
        'removed': {},
        'summary': []
    }
    
    try:
        # Find all unique keys
        all_keys = set(old_data.keys()) | set(new_data.keys())
        
        for key in all_keys:
            old_value = old_data.get(key)
            new_value = new_data.get(key)
            
            if key not in old_data:
                # New field added
                changes['added'][key] = new_value
                changes['summary'].append(f"Added {key}")
            elif key not in new_data:
                # Field removed
                changes['removed'][key] = old_value
                changes['summary'].append(f"Removed {key}")
            elif old_value != new_value:
                # Field modified
                changes['modified'][key] = {
                    'old': old_value,
                    'new': new_value
                }
                changes['summary'].append(f"Changed {key}")
        
        # Add change count
        changes['change_count'] = len(changes['added']) + len(changes['modified']) + len(changes['removed'])
        
    except Exception as e:
        logger.warning(f"Error extracting changes: {e}")
        changes['error'] = str(e)
    
    return changes


def format_audit_details(details: Dict[str, Any]) -> str:
    """
    Format audit details for display
    
    Args:
        details: Dictionary containing audit details
    
    Returns:
        Formatted string representation
    """
    try:
        if not details:
            return "No details available"
        
        if isinstance(details, dict):
            # Format as readable JSON
            return json.dumps(details, indent=2, default=str)
        else:
            return str(details)
            
    except Exception as e:
        logger.warning(f"Error formatting audit details: {e}")
        return str(details)


def validate_audit_config() -> Dict[str, Any]:
    """
    Validate audit trail configuration
    
    Returns:
        Dictionary containing validation results
    """
    config = getattr(settings, 'AUDIT_TRAIL_CONFIG', {})
    
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'config': config
    }
    
    try:
        # Check if audit trail is enabled
        if not config.get('ENABLED', True):
            validation_result['warnings'].append("Audit trail is disabled")
        
        # Check required settings
        required_settings = ['AUDIT_MODEL']
        for setting in required_settings:
            if not config.get(setting):
                validation_result['errors'].append(f"Missing required setting: {setting}")
                validation_result['is_valid'] = False
        
        # Check model paths
        if config.get('AUDIT_MODEL'):
            try:
                from django.apps import apps
                app_label, model_name = config['AUDIT_MODEL'].split('.')
                apps.get_model(app_label, model_name)
            except Exception as e:
                validation_result['errors'].append(f"Invalid AUDIT_MODEL: {e}")
                validation_result['is_valid'] = False
        
        # Check optional settings
        if config.get('RETENTION_DAYS'):
            retention_days = config['RETENTION_DAYS']
            if not isinstance(retention_days, int) or retention_days < 1:
                validation_result['warnings'].append("RETENTION_DAYS should be a positive integer")
        
        if config.get('BULK_CREATE_BATCH_SIZE'):
            batch_size = config['BULK_CREATE_BATCH_SIZE']
            if not isinstance(batch_size, int) or batch_size < 1:
                validation_result['warnings'].append("BULK_CREATE_BATCH_SIZE should be a positive integer")
        
    except Exception as e:
        validation_result['errors'].append(f"Error validating configuration: {e}")
        validation_result['is_valid'] = False
    
    return validation_result


def get_audit_model_fields() -> List[str]:
    """
    Get list of fields available in the audit model
    
    Returns:
        List of field names
    """
    try:
        from .operations import get_audit_model
        
        audit_model = get_audit_model()
        return [field.name for field in audit_model._meta.fields]
        
    except Exception as e:
        logger.warning(f"Error getting audit model fields: {e}")
        return []


def serialize_for_audit(obj: Any) -> Any:
    """
    Serialize an object for audit logging
    
    Args:
        obj: Object to serialize
    
    Returns:
        Serialized representation
    """
    try:
        if obj is None:
            return None
        
        # Handle Django model instances
        if hasattr(obj, '_meta'):
            # Django model instance
            serialized = {}
            for field in obj._meta.fields:
                if not field.name.endswith('password'):  # Skip sensitive fields
                    value = getattr(obj, field.name)
                    serialized[field.name] = serialize_for_audit(value)
            return serialized
        
        # Handle common Python types
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: serialize_for_audit(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [serialize_for_audit(item) for item in obj]
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            # Generic object with attributes
            return serialize_for_audit(obj.__dict__)
        else:
            # Fall back to string representation
            return str(obj)
            
    except Exception as e:
        logger.warning(f"Error serializing object for audit: {e}")
        return str(obj)


def create_audit_context(request: HttpRequest, **kwargs) -> Dict[str, Any]:
    """
    Create audit context dictionary from request and additional data
    
    Args:
        request: Django request object
        **kwargs: Additional context data
    
    Returns:
        Audit context dictionary
    """
    context = {
        'trace_id': get_trace_id(request),
        'ip_address': get_client_ip(request),
        'user_agent': get_user_agent(request),
        'request_path': getattr(request, 'path', ''),
        'request_method': getattr(request, 'method', ''),
        'timestamp': None,  # Will be set by model
    }
    
    # Add any additional context
    context.update(kwargs)
    
    # Sanitize the context
    return sanitize_audit_data(context)


def batch_process_audit_entries(entries: List[Dict[str, Any]], batch_size: int = None) -> List[List[Dict[str, Any]]]:
    """
    Split audit entries into batches for processing
    
    Args:
        entries: List of audit entry dictionaries
        batch_size: Size of each batch
    
    Returns:
        List of batches
    """
    if batch_size is None:
        config = getattr(settings, 'AUDIT_TRAIL_CONFIG', {})
        batch_size = config.get('BULK_CREATE_BATCH_SIZE', AuditTrailConstants.BULK_CREATE_BATCH_SIZE)
    
    batches = []
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]
        batches.append(batch)
    
    return batches
