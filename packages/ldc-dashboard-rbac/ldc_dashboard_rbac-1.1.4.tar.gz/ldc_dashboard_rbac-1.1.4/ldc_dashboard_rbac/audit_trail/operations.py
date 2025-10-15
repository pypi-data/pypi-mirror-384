"""
Database operations for audit trail functionality
"""
from django.db import transaction
from django.db.models import Q
from django.apps import apps
from django.conf import settings
from typing import Dict, Any, List, Optional, Union
import logging

from .constants import AuditTrailConstants, MessageCodes

logger = logging.getLogger(__name__)


class AuditTrailOperationError(Exception):
    """Custom exception for audit trail operations"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or MessageCodes.ERROR
        super().__init__(self.message)


def get_audit_model():
    """Get the audit trail model from configuration"""
    try:
        config = getattr(settings, 'AUDIT_TRAIL_CONFIG', {})
        model_path = config.get('AUDIT_MODEL')
        
        if not model_path:
            # Return None instead of raising error
            return None
        
        app_label, model_name = model_path.split('.')
        return apps.get_model(app_label, model_name)
        
    except Exception as e:
        logger.warning(f"Could not get audit model: {e}")
        return None


def create_audit_trail_entry(
    dashboard_user=None,
    user_role: str = None,
    action_type: str = None,
    entity_type: str = None,
    entity_id: int = None,
    details: Dict[str, Any] = None,
    trace_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    old_values: Dict[str, Any] = None,
    new_values: Dict[str, Any] = None,
    is_successful: bool = True,
    error_message: str = None,
    content_object=None,
    **kwargs
) -> Any:
    """
    Create an audit trail entry
    
    Args:
        dashboard_user: User instance
        user_role: Role of the user
        action_type: Type of action performed
        entity_type: Type of entity affected
        entity_id: ID of the entity
        details: Additional details dictionary
        trace_id: Request trace ID
        ip_address: User's IP address
        user_agent: User agent string
        old_values: Previous values before change
        new_values: New values after change
        is_successful: Whether the action was successful
        error_message: Error message if action failed
        content_object: Django model instance for generic foreign key
        **kwargs: Additional fields
    
    Returns:
        AuditTrail instance
    
    Raises:
        AuditTrailOperationError: If creation fails
    """
    try:
        AuditModel = get_audit_model()
        
        if not AuditModel:
            logger.warning("Audit trail not configured, skipping entry creation")
            return None

        # Prepare audit data
        audit_data = {
            'dashboard_user': dashboard_user,
            'user_role': user_role,
            'action_type': action_type,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'details': details or {},
            'trace_id': trace_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'old_values': old_values or {},
            'new_values': new_values or {},
            'is_successful': is_successful,
            'error_message': error_message,
        }
        
        # Add content object if provided
        if content_object:
            from django.contrib.contenttypes.models import ContentType
            audit_data['content_type'] = ContentType.objects.get_for_model(content_object)
            audit_data['object_id'] = content_object.pk
        
        # Add any additional kwargs
        audit_data.update(kwargs)
        
        # Remove None values
        audit_data = {k: v for k, v in audit_data.items() if v is not None}
        
        with transaction.atomic():
            audit_entry = AuditModel.objects.create(**audit_data)
            
        logger.info(f"Audit trail entry created: {audit_entry.id}")
        return audit_entry
        
    except Exception as e:
        error_msg = f"Error creating audit trail entry: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise AuditTrailOperationError(error_msg, MessageCodes.CREATION_FAILED)


def get_audit_trail_logs(
    filters: Dict[str, Any] = None,
    excludes: Dict[str, Any] = None,
    values_list: List[str] = None,
    select_related: Union[str, List[str]] = None,
    prefetch_related: Union[str, List[str]] = None,
    q_expression: Q = None,
    order_by: Union[str, List[str]] = None,
    limit: int = None,
    offset: int = None
):
    """
    Get audit trail logs with flexible filtering and querying options
    
    Args:
        filters: Dictionary of field filters
        excludes: Dictionary of field excludes
        values_list: List of fields to return as values
        select_related: Fields to select_related
        prefetch_related: Fields to prefetch_related
        q_expression: Q object for complex queries
        order_by: Fields to order by
        limit: Maximum number of records to return
        offset: Number of records to skip
    
    Returns:
        QuerySet or values list depending on values_list parameter
    
    Raises:
        AuditTrailOperationError: If query fails
    """
    try:
        AuditModel = get_audit_model()
        
        if not AuditModel:
            logger.warning("Audit trail not configured, skipping log retrieval")
            return []

        # Initialize defaults
        filters = filters or {}
        excludes = excludes or {}
        q_expression = q_expression or Q()
        values_list = values_list or []
        
        # Start with base queryset
        queryset = AuditModel.objects.all()
        
        # Apply select_related
        if select_related:
            if isinstance(select_related, str):
                queryset = queryset.select_related(select_related)
            else:
                queryset = queryset.select_related(*select_related)
        
        # Apply prefetch_related
        if prefetch_related:
            if isinstance(prefetch_related, str):
                queryset = queryset.prefetch_related(prefetch_related)
            else:
                queryset = queryset.prefetch_related(*prefetch_related)
        
        # Apply filters and excludes
        queryset = queryset.filter(q_expression, **filters).exclude(**excludes)
        
        # Apply ordering
        if order_by:
            if isinstance(order_by, str):
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by(*order_by)
        else:
            # Default ordering by creation date descending
            queryset = queryset.order_by('-created_dtm')
        
        # Apply limit and offset
        if offset is not None and limit is not None:
            queryset = queryset[offset:offset + limit]
        elif limit is not None:
            queryset = queryset[:limit]
        elif offset is not None:
            queryset = queryset[offset:]
        
        # Return values if specified
        fields_count = len(values_list)
        if fields_count == 1:
            return queryset.values_list(*values_list, flat=True)
        elif fields_count > 1:
            return queryset.values(*values_list)
        else:
            return queryset
            
    except Exception as e:
        error_msg = f"Error fetching audit trail logs: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise AuditTrailOperationError(error_msg, MessageCodes.RETRIEVAL_FAILED)


def bulk_create_audit_entries(audit_entries: List[Dict[str, Any]]) -> List[Any]:
    """
    Bulk create audit trail entries for better performance
    
    Args:
        audit_entries: List of audit entry dictionaries
    
    Returns:
        List of created AuditTrail instances
    
    Raises:
        AuditTrailOperationError: If bulk creation fails
    """
    try:
        AuditModel = get_audit_model()
        
        if not AuditModel:
            logger.warning("Audit trail not configured, skipping bulk creation")
            return []

        if not audit_entries:
            return []
        
        # Prepare audit objects
        audit_objects = []
        for entry_data in audit_entries:
            # Remove None values
            clean_data = {k: v for k, v in entry_data.items() if v is not None}
            audit_objects.append(AuditModel(**clean_data))
        
        # Bulk create with batch size
        batch_size = getattr(
            settings,
            'AUDIT_TRAIL_CONFIG',
            {}
        ).get('BULK_CREATE_BATCH_SIZE', AuditTrailConstants.BULK_CREATE_BATCH_SIZE)
        
        with transaction.atomic():
            created_entries = AuditModel.objects.bulk_create(
                audit_objects,
                batch_size=batch_size
            )
        
        logger.info(f"Bulk created {len(created_entries)} audit trail entries")
        return created_entries
        
    except Exception as e:
        error_msg = f"Error bulk creating audit trail entries: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise AuditTrailOperationError(error_msg, MessageCodes.CREATION_FAILED)


def get_audit_stats(
    start_date=None,
    end_date=None,
    user=None,
    action_types: List[str] = None,
    entity_types: List[str] = None
) -> Dict[str, Any]:
    """
    Get audit trail statistics
    
    Args:
        start_date: Start date for filtering
        end_date: End date for filtering
        user: User to filter by
        action_types: List of action types to include
        entity_types: List of entity types to include
    
    Returns:
        Dictionary with audit statistics
    
    Raises:
        AuditTrailOperationError: If stats query fails
    """
    try:
        from django.db.models import Count, Q
        
        AuditModel = get_audit_model()
        
        if not AuditModel:
            logger.warning("Audit trail not configured, skipping stats retrieval")
            return {}

        # Build base query
        filters = {}
        if start_date:
            filters['created_dtm__gte'] = start_date
        if end_date:
            filters['created_dtm__lte'] = end_date
        if user:
            filters['dashboard_user'] = user
        if action_types:
            filters['action_type__in'] = action_types
        if entity_types:
            filters['entity_type__in'] = entity_types
        
        queryset = AuditModel.objects.filter(**filters)
        
        # Calculate statistics
        stats = {
            'total_entries': queryset.count(),
            'successful_entries': queryset.filter(is_successful=True).count(),
            'failed_entries': queryset.filter(is_successful=False).count(),
            'action_type_breakdown': dict(
                queryset.values('action_type').annotate(count=Count('id')).values_list('action_type', 'count')
            ),
            'entity_type_breakdown': dict(
                queryset.values('entity_type').annotate(count=Count('id')).values_list('entity_type', 'count')
            ),
            'user_breakdown': dict(
                queryset.values('dashboard_user__username').annotate(count=Count('id')).values_list('dashboard_user__username', 'count')
            ) if hasattr(AuditModel, 'dashboard_user') else {},
        }
        
        return stats
        
    except Exception as e:
        error_msg = f"Error getting audit trail statistics: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise AuditTrailOperationError(error_msg, MessageCodes.RETRIEVAL_FAILED)


def cleanup_old_audit_entries(retention_days: int = None) -> int:
    """
    Clean up old audit trail entries based on retention policy
    
    Args:
        retention_days: Number of days to retain entries
    
    Returns:
        Number of deleted entries
    
    Raises:
        AuditTrailOperationError: If cleanup fails
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        AuditModel = get_audit_model()
        
        if not AuditModel:
            logger.warning("Audit trail not configured, skipping cleanup")
            return 0

        if retention_days is None:
            retention_days = getattr(
                settings,
                'AUDIT_TRAIL_CONFIG',
                {}
            ).get('RETENTION_DAYS', AuditTrailConstants.DEFAULT_RETENTION_DAYS)
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        with transaction.atomic():
            deleted_count, _ = AuditModel.objects.filter(
                created_dtm__lt=cutoff_date
            ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old audit trail entries")
        return deleted_count
        
    except Exception as e:
        error_msg = f"Error cleaning up audit trail entries: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise AuditTrailOperationError(error_msg, MessageCodes.ERROR)
