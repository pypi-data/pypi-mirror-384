"""
Django signals for automatic audit trail logging
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
import logging

from .helpers import create_audit_log_helper
from .constants import AuditTrailActionTypes, AuditTrailEntityTypes
from .utils import serialize_for_audit

logger = logging.getLogger(__name__)


def get_audit_config():
    """Get audit trail configuration"""
    return getattr(settings, 'AUDIT_TRAIL_CONFIG', {})


def should_track_model(model_class):
    """Check if a model should be tracked"""
    config = get_audit_config()
    
    # Check if signals are enabled
    if not config.get('AUTO_TRACK_CHANGES', False):
        return False
    
    # Get tracked models from config
    tracked_models = config.get('TRACKED_MODELS', [])
    model_path = f"{model_class._meta.app_label}.{model_class._meta.model_name}"
    
    return model_path in tracked_models


@receiver(post_save)
def audit_model_save(sender, instance, created, **kwargs):
    """Audit model save operations"""
    try:
        if not should_track_model(sender):
            return
        
        # Determine action type
        action_type = AuditTrailActionTypes.CREATE if created else AuditTrailActionTypes.UPDATE
        
        # Get entity type
        entity_type = sender._meta.model_name
        
        # Create audit entry
        # Note: This would need a request object, which is not available in signals
        # You might need to use thread-local storage or another mechanism
        # For now, we'll skip the request-dependent parts
        
        logger.info(f"Model {sender._meta.label} {action_type}: {instance.pk}")
        
    except Exception as e:
        logger.error(f"Error in audit_model_save signal: {e}")


@receiver(post_delete)
def audit_model_delete(sender, instance, **kwargs):
    """Audit model delete operations"""
    try:
        if not should_track_model(sender):
            return
        
        # Get entity type
        entity_type = sender._meta.model_name
        
        # Serialize the deleted instance
        deleted_data = serialize_for_audit(instance)
        
        # Create audit entry
        logger.info(f"Model {sender._meta.label} deleted: {instance.pk}")
        
    except Exception as e:
        logger.error(f"Error in audit_model_delete signal: {e}")


@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    """Audit user login"""
    try:
        config = get_audit_config()
        if not config.get('TRACK_AUTH_EVENTS', True):
            return
        
        create_audit_log_helper(
            request=request,
            action_type=AuditTrailActionTypes.LOGIN,
            entity_type=AuditTrailEntityTypes.USER,
            entity_id=user.pk,
            details={
                'username': getattr(user, 'username', str(user)),
                'login_method': 'standard'
            },
            user_instance=user
        )
        
    except Exception as e:
        logger.error(f"Error in audit_user_login signal: {e}")


@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    """Audit user logout"""
    try:
        config = get_audit_config()
        if not config.get('TRACK_AUTH_EVENTS', True):
            return
        
        if user:  # User might be None in some cases
            create_audit_log_helper(
                request=request,
                action_type=AuditTrailActionTypes.LOGOUT,
                entity_type=AuditTrailEntityTypes.USER,
                entity_id=user.pk,
                details={
                    'username': getattr(user, 'username', str(user)),
                    'logout_method': 'standard'
                },
                user_instance=user
            )
        
    except Exception as e:
        logger.error(f"Error in audit_user_logout signal: {e}")


@receiver(user_login_failed)
def audit_user_login_failed(sender, credentials, request, **kwargs):
    """Audit failed login attempts"""
    try:
        config = get_audit_config()
        if not config.get('TRACK_AUTH_EVENTS', True):
            return
        
        create_audit_log_helper(
            request=request,
            action_type=AuditTrailActionTypes.LOGIN,
            entity_type=AuditTrailEntityTypes.USER,
            entity_id=0,  # No user ID for failed login
            details={
                'username': credentials.get('username', 'unknown'),
                'login_method': 'standard',
                'failure_reason': 'invalid_credentials'
            },
            is_successful=False,
            error_message='Login failed: Invalid credentials'
        )
        
    except Exception as e:
        logger.error(f"Error in audit_user_login_failed signal: {e}")


# Custom signal for RBAC events
def audit_rbac_event(sender, request, action_type, entity_type, entity_id, 
                    details=None, user=None, is_successful=True, **kwargs):
    """
    Custom signal for RBAC-specific events
    
    Usage:
        from ldc_dashboard_rbac.audit_trail.signals import audit_rbac_event
        
        audit_rbac_event.send(
            sender=MyView,
            request=request,
            action_type=AuditTrailActionTypes.PERMISSION_GRANTED,
            entity_type=AuditTrailEntityTypes.FEATURE,
            entity_id=feature.id,
            details={'feature_name': feature.name},
            user=request.user
        )
    """
    try:
        create_audit_log_helper(
            request=request,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            user_instance=user,
            is_successful=is_successful
        )
        
    except Exception as e:
        logger.error(f"Error in audit_rbac_event signal: {e}")


# Make the custom signal available
import django.dispatch
audit_rbac_event = django.dispatch.Signal()
audit_rbac_event.connect(audit_rbac_event)
