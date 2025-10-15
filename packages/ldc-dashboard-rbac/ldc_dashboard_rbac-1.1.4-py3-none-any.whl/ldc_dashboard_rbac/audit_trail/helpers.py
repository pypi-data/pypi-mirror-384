"""
Helper functions for audit trail functionality
"""
from django.db.models import Q
from django.conf import settings
from typing import Dict, Any, Optional, List
import logging

from .operations import create_audit_trail_entry, get_audit_trail_logs, AuditTrailOperationError
from .constants import MessageCodes, AuditTrailConstants
from .utils import get_client_ip, get_user_agent, get_trace_id, sanitize_audit_data

logger = logging.getLogger(__name__)


def create_audit_log_helper(
    request,
    action_type: str,
    entity_type: str,
    entity_id: int,
    details: Dict[str, Any] = None,
    user_instance=None,
    old_values: Dict[str, Any] = None,
    new_values: Dict[str, Any] = None,
    is_successful: bool = True,
    error_message: str = None,
    content_object=None
) -> Optional[Any]:
    """
    A robust helper to create an audit log entry.
    
    This function handles user context extraction, error handling, and provides
    a clean interface for creating audit logs from Django views.
    
    Args:
        request: Django request object
        action_type: Type of action performed
        entity_type: Type of entity affected
        entity_id: ID of the entity
        details: Additional details dictionary
        user_instance: User instance (if not provided, extracted from request)
        old_values: Previous values before change
        new_values: New values after change
        is_successful: Whether the action was successful
        error_message: Error message if action failed
        content_object: Django model instance for generic foreign key
    
    Returns:
        AuditTrail instance if successful, None if failed
    """
    try:
        # Get audit trail configuration
        config = getattr(settings, 'AUDIT_TRAIL_CONFIG', {})
        
        # Check if audit trail is enabled
        if not config.get('ENABLED', True):
            return None
        
        # Get user context
        dashboard_user_instance = user_instance
        user_context = None
        
        # Try to get user context from request
        try:
            # Extract user from request
            if not dashboard_user_instance and hasattr(request, 'user') and request.user.is_authenticated:
                dashboard_user_instance = request.user
                
            # Get additional user context if available
            if hasattr(request, 'user_context'):
                user_context = request.user_context
            elif dashboard_user_instance:
                user_context = {
                    'username': getattr(dashboard_user_instance, 'username', str(dashboard_user_instance)),
                    'role': getattr(dashboard_user_instance, 'role', 'unknown'),
                    'is_super_admin': getattr(dashboard_user_instance, 'is_superadmin', False),
                }
        except Exception as e:
            logger.warning(f"Could not extract user context from request: {e}")
        
        if not dashboard_user_instance:
            logger.warning("Audit log skipped: Could not find user instance")
            return None
        
        # Get request information
        trace_id = get_trace_id(request)
        ip_address = get_client_ip(request) if config.get('TRACK_IP_ADDRESS', True) else None
        user_agent = get_user_agent(request) if config.get('TRACK_USER_AGENT', True) else None
        
        # Prepare details
        audit_details = details or {}
        
        # Add request context to details
        if hasattr(request, 'path'):
            audit_details[AuditTrailConstants.DetailsKeys.REQUEST_PATH] = request.path
        if hasattr(request, 'method'):
            audit_details[AuditTrailConstants.DetailsKeys.REQUEST_METHOD] = request.method
        
        # Sanitize sensitive data
        audit_details = sanitize_audit_data(audit_details)
        if old_values:
            old_values = sanitize_audit_data(old_values)
        if new_values:
            new_values = sanitize_audit_data(new_values)
        
        # Create audit entry
        audit_entry = create_audit_trail_entry(
            dashboard_user=dashboard_user_instance,
            user_role=user_context.get('role') if user_context else None,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=int(entity_id),
            details=audit_details,
            trace_id=trace_id,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_values,
            new_values=new_values,
            is_successful=is_successful,
            error_message=error_message,
            content_object=content_object,
        )
        
        logger.info(f"Successfully created audit log for action: {action_type}")
        return audit_entry
        
    except Exception as e:
        # Log the error but do not re-raise it.
        # This ensures that a failure in audit logging does not fail the primary operation.
        logger.error(f"Failed to create audit log for action {action_type}: {e}", exc_info=True)
        return None


def get_audit_trail_list_helper(validated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function for retrieving audit trail lists with pagination and filtering.
    
    Args:
        validated_data: Dictionary containing query parameters
    
    Returns:
        Dictionary with audit logs and pagination info
    """
    try:
        # Extract pagination parameters
        page = validated_data.pop('page', 1)
        limit = validated_data.pop('limit', AuditTrailConstants.DEFAULT_PAGE_SIZE)
        offset = (page - 1) * limit
        
        # Prepare filters for the query
        filters = {}
        q_expression = Q()
        
        # Handle username filtering (related field)
        if validated_data.get('user_username'):
            q_expression &= Q(dashboard_user__username__icontains=validated_data['user_username'])
        
        # Handle action type filtering
        if validated_data.get('action_type'):
            filters['action_type'] = validated_data['action_type']
        
        # Handle entity type filtering
        if validated_data.get('entity_type'):
            filters['entity_type'] = validated_data['entity_type']
        
        # Handle entity ID filtering
        if validated_data.get('entity_id'):
            filters['entity_id'] = validated_data['entity_id']
        
        # Handle date range filtering
        if validated_data.get('start_date'):
            filters['created_dtm__gte'] = validated_data['start_date']
        
        if validated_data.get('end_date'):
            filters['created_dtm__lte'] = validated_data['end_date']
        
        # Handle success status filtering
        if validated_data.get('is_successful') is not None:
            filters['is_successful'] = validated_data['is_successful']
        
        # Handle trace ID filtering
        if validated_data.get('trace_id'):
            filters['trace_id'] = validated_data['trace_id']
        
        # Fetch the logs
        logs_qs = get_audit_trail_logs(
            filters=filters,
            select_related='dashboard_user',
            q_expression=q_expression,
            limit=limit,
            offset=offset
        )
        
        # Get total count for pagination
        total_logs_qs = get_audit_trail_logs(
            filters=filters,
            q_expression=q_expression
        )
        total_records = total_logs_qs.count()
        
        # Serialize the queryset into a list of dictionaries
        serialized_logs = []
        for log in logs_qs:
            log_data = {
                "id": log.id,
                "username": getattr(log.dashboard_user, 'username', 'Unknown') if log.dashboard_user else 'System',
                "user_role": log.user_role,
                "action_type": log.action_type,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "trace_id": log.trace_id,
                "ip_address": log.ip_address,
                "is_successful": log.is_successful,
                "error_message": log.error_message,
                "created_dtm": log.created_dtm.isoformat() if log.created_dtm else None,
                "updated_dtm": log.updated_dtm.isoformat() if log.updated_dtm else None,
            }
            
            # Add change summary if available
            if hasattr(log, 'get_changes_summary'):
                log_data["changes_summary"] = log.get_changes_summary()
            
            serialized_logs.append(log_data)
        
        response_data = {
            "audit_logs": serialized_logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit,
            }
        }
        
        return {
            'message_code': MessageCodes.SUCCESS,
            'response_data': response_data
        }
        
    except AuditTrailOperationError as e:
        logger.error(f"Audit trail operation error in get_audit_trail_list_helper: {e}")
        return {
            'message_code': e.code,
            'exception': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_audit_trail_list_helper: {e}", exc_info=True)
        return {
            'message_code': MessageCodes.ERROR,
            'exception': str(e)
        }


def get_audit_trail_context_helper(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to get audit trail page context data.
    
    Args:
        user_context: Dictionary containing user context information
    
    Returns:
        Dictionary with context data for audit trail pages
    """
    try:
        if not user_context:
            return {
                'message_code': MessageCodes.PERMISSION_DENIED,
                'message': 'Authentication required'
            }
        
        current_role = user_context.get('current_role', user_context.get('role'))
        
        # Check if user has admin privileges (admin or super_admin)
        # Adjust this based on your role system
        admin_roles = ['admin', 'super_admin', 'superadmin']
        if current_role not in admin_roles:
            return {
                'message_code': MessageCodes.PERMISSION_DENIED,
                'message': 'Access denied. Admin privileges required.'
            }
        
        # Prepare context data for template
        context_data = {
            'username': user_context.get('username'),
            'name': user_context.get('name'),
            'role': user_context.get('role'),
            'is_super_admin': user_context.get('is_super_admin', False),
            'page_title': 'Audit Trails',
            'page_description': 'View system audit trails and user activity logs',
            'available_actions': _get_available_action_types(),
            'available_entities': _get_available_entity_types(),
        }
        
        return {
            'message_code': MessageCodes.SUCCESS,
            'response_data': context_data
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_audit_trail_context_helper: {str(e)}", exc_info=True)
        return {
            'message_code': MessageCodes.ERROR,
            'message': 'Internal server error'
        }


def get_user_audit_summary_helper(user, days: int = 30) -> Dict[str, Any]:
    """
    Get audit trail summary for a specific user
    
    Args:
        user: User instance
        days: Number of days to look back
    
    Returns:
        Dictionary with user audit summary
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get user audit logs
        filters = {
            'dashboard_user': user,
            'created_dtm__gte': start_date,
            'created_dtm__lte': end_date,
        }
        
        logs_qs = get_audit_trail_logs(filters=filters)
        
        # Calculate summary statistics
        total_actions = logs_qs.count()
        successful_actions = logs_qs.filter(is_successful=True).count()
        failed_actions = logs_qs.filter(is_successful=False).count()
        
        # Get action breakdown
        from django.db.models import Count
        action_breakdown = dict(
            logs_qs.values('action_type').annotate(
                count=Count('id')
            ).values_list('action_type', 'count')
        )
        
        # Get recent activities (last 10)
        recent_activities = []
        for log in logs_qs.order_by('-created_dtm')[:10]:
            recent_activities.append({
                'action_type': log.action_type,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'is_successful': log.is_successful,
                'created_dtm': log.created_dtm.isoformat(),
            })
        
        summary_data = {
            'user': {
                'username': getattr(user, 'username', str(user)),
                'name': getattr(user, 'name', ''),
                'role': getattr(user, 'role', ''),
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days,
            },
            'statistics': {
                'total_actions': total_actions,
                'successful_actions': successful_actions,
                'failed_actions': failed_actions,
                'success_rate': (successful_actions / total_actions * 100) if total_actions > 0 else 0,
            },
            'action_breakdown': action_breakdown,
            'recent_activities': recent_activities,
        }
        
        return {
            'message_code': MessageCodes.SUCCESS,
            'response_data': summary_data
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_audit_summary_helper: {e}", exc_info=True)
        return {
            'message_code': MessageCodes.ERROR,
            'exception': str(e)
        }


def _get_available_action_types() -> List[Dict[str, str]]:
    """Get list of available action types for UI"""
    from .constants import AuditTrailActionTypes
    
    return [
        {'value': choice[0], 'label': choice[1]}
        for choice in AuditTrailActionTypes.CHOICES
    ]


def _get_available_entity_types() -> List[Dict[str, str]]:
    """Get list of available entity types for UI"""
    from .constants import AuditTrailEntityTypes
    
    return [
        {'value': choice[0], 'label': choice[1]}
        for choice in AuditTrailEntityTypes.COMMON_CHOICES
    ]
