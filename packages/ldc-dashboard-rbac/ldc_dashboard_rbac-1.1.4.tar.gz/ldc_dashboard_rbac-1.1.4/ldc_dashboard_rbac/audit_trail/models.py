"""
Abstract models for audit trail functionality
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
import json

from ..base_models import DefaultTimeStamp
from .constants import AuditTrailActionTypes, AuditTrailEntityTypes, AuditTrailFieldLengths


class AbstractAuditTrailManager(models.Manager):
    """
    Abstract manager for audit trail operations
    
    Provides common query methods and utilities for audit trail models.
    """
    
    def create_entry(self, user=None, action_type=None, entity_type=None, 
                    entity_id=None, details=None, **kwargs):
        """
        Create an audit trail entry
        
        Args:
            user: User instance
            action_type: Type of action
            entity_type: Type of entity
            entity_id: ID of entity
            details: Additional details dict
            **kwargs: Additional fields
        
        Returns:
            AuditTrail instance
        """
        return self.create(
            dashboard_user=user,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            **kwargs
        )
    
    def for_user(self, user):
        """Get audit trails for a specific user"""
        return self.filter(dashboard_user=user)
    
    def for_entity(self, entity_type, entity_id):
        """Get audit trails for a specific entity"""
        return self.filter(entity_type=entity_type, entity_id=entity_id)
    
    def for_action_type(self, action_type):
        """Get audit trails for a specific action type"""
        return self.filter(action_type=action_type)
    
    def successful_only(self):
        """Get only successful audit trails"""
        return self.filter(is_successful=True)
    
    def failed_only(self):
        """Get only failed audit trails"""
        return self.filter(is_successful=False)
    
    def recent(self, days=30):
        """Get recent audit trails within specified days"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_dtm__gte=cutoff_date)
    
    def by_trace_id(self, trace_id):
        """Get audit trails by trace ID"""
        return self.filter(trace_id=trace_id)


class AbstractAuditTrail(DefaultTimeStamp):
    """
    Abstract base model for audit trail entries
    
    This model tracks user actions, system events, and data changes.
    It's designed to be generic and reusable across different projects.
    
    Usage in concrete models:
    
    class AuditTrail(AbstractAuditTrail):
        dashboard_user = models.ForeignKey(
            'dashboard.DashboardUser',  # Your user model
            on_delete=models.SET_NULL,
            null=True,
            related_name='audit_trails'
        )
        
        class Meta:
            db_table = 'audit_trail'
            ordering = ['-created_dtm']
            indexes = [
                models.Index(fields=['action_type', 'created_dtm']),
                models.Index(fields=['entity_type', 'entity_id']),
                models.Index(fields=['trace_id']),
            ]
    """
    
    # Add the user field back
    dashboard_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_trails',
        help_text="User who performed the action"
    )
    
    # User role at the time of action
    user_role = models.CharField(
        max_length=AuditTrailFieldLengths.USER_ROLE_MAX_LENGTH,
        null=True,
        blank=True,
        help_text="Role of the user at the time of action"
    )
    
    # Action information
    action_type = models.CharField(
        max_length=AuditTrailFieldLengths.ACTION_TYPE_MAX_LENGTH,
        choices=AuditTrailActionTypes.CHOICES,
        help_text="Type of action performed"
    )
    
    # Entity information
    entity_type = models.CharField(
        max_length=AuditTrailFieldLengths.ENTITY_TYPE_MAX_LENGTH,
        help_text="Type of entity affected by the action"
    )
    entity_id = models.PositiveIntegerField(
        help_text="ID of the entity affected by the action"
    )
    
    # Optional: Generic foreign key for more flexible entity references
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        help_text="Content type of the affected entity"
    )
    object_id = models.PositiveIntegerField(
        null=True,
        help_text="ID of the affected object"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional details
    details = models.JSONField(
        default=dict,
        help_text="Additional details about the action in JSON format"
    )
    
    # Request tracking
    trace_id = models.CharField(
        max_length=AuditTrailFieldLengths.TRACE_ID_MAX_LENGTH,
        null=True,
        help_text="Trace ID for request tracking"
    )
    
    # IP and User Agent
    ip_address = models.GenericIPAddressField(
        null=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        null=True,
        help_text="User agent string"
    )
    
    # Change tracking
    old_values = models.JSONField(
        default=dict,
        help_text="Previous values before the change"
    )
    new_values = models.JSONField(
        default=dict,
        help_text="New values after the change"
    )
    
    # Status and metadata
    is_successful = models.BooleanField(
        default=True,
        help_text="Whether the action was successful"
    )
    error_message = models.TextField(
        null=True,
        help_text="Error message if action failed"
    )
    
    # Use custom manager
    objects = AbstractAuditTrailManager()
    
    class Meta:
        abstract = True
        ordering = ['-created_dtm']
    
    def __str__(self):
        return f"{self.action_type} on {self.entity_type}({self.entity_id}) at {self.created_dtm}"
    
    def get_details_display(self):
        """Get formatted details for display"""
        if not self.details:
            return "No details"
        
        try:
            if isinstance(self.details, dict):
                return json.dumps(self.details, indent=2)
            return str(self.details)
        except Exception:
            return str(self.details)
    
    def get_changes_summary(self):
        """Get a summary of changes made"""
        if not self.old_values and not self.new_values:
            return "No changes tracked"
        
        changes = []
        
        # Compare old and new values
        all_fields = set(self.old_values.keys()) | set(self.new_values.keys())
        
        for field in all_fields:
            old_val = self.old_values.get(field, 'N/A')
            new_val = self.new_values.get(field, 'N/A')
            
            if old_val != new_val:
                changes.append(f"{field}: {old_val} → {new_val}")
        
        return "; ".join(changes) if changes else "No changes detected"
    
    def is_create_action(self):
        """Check if this is a create action"""
        return self.action_type in [
            AuditTrailActionTypes.CREATE,
            AuditTrailActionTypes.REGISTER,
            AuditTrailActionTypes.APPROVE,
        ]
    
    def is_update_action(self):
        """Check if this is an update action"""
        return self.action_type in [
            AuditTrailActionTypes.UPDATE,
            AuditTrailActionTypes.MODIFY,
            AuditTrailActionTypes.ACTIVATE,
            AuditTrailActionTypes.DEACTIVATE,
        ]
    
    def is_delete_action(self):
        """Check if this is a delete action"""
        return self.action_type in [
            AuditTrailActionTypes.DELETE,
            AuditTrailActionTypes.REJECT,
        ]
    
    def is_access_action(self):
        """Check if this is an access action"""
        return self.action_type in [
            AuditTrailActionTypes.LOGIN,
            AuditTrailActionTypes.LOGOUT,
            AuditTrailActionTypes.VIEW,
            AuditTrailActionTypes.ACCESS,
        ]
