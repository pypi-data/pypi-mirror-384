"""
Signals for RBAC (cache removed for immediate effects)
"""
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.apps import apps
from ldc_dashboard_rbac.permissions import get_rbac_config
import logging

logger = logging.getLogger(__name__)


def get_rbac_models():
    """Get RBAC models dynamically"""
    try:
        config = get_rbac_config()
        feature_model = apps.get_model(config.get('FEATURE_MODEL', 'dashboard.Feature'))
        group_model = apps.get_model(config.get('GROUP_MODEL', 'dashboard.Group'))
        user_group_model = apps.get_model(config.get('USER_GROUP_MODEL', 'dashboard.UserGroup'))
        permission_model = apps.get_model(config.get('GROUP_FEATURE_PERMISSION_MODEL', 'dashboard.GroupFeaturePermission'))
        
        return [feature_model, group_model, user_group_model, permission_model]
    except Exception as e:
        logger.error(f"Error getting RBAC models: {e}")
        return []


@receiver(post_save)
def log_rbac_changes_on_save(sender, instance, created, **kwargs):
    """Log RBAC changes for debugging (no cache clearing needed)"""
    try:
        rbac_models = get_rbac_models()
        
        # Log changes to RBAC-related models
        if sender in rbac_models:
            action = "created" if created else "updated"
            logger.info(f"RBAC change: {sender.__name__} {action} - {instance}")
            
    except Exception as e:
        logger.error(f"Error logging RBAC change on save: {e}")


@receiver(post_delete)
def log_rbac_changes_on_delete(sender, instance, **kwargs):
    """Log RBAC changes for debugging (no cache clearing needed)"""
    try:
        rbac_models = get_rbac_models()
        
        # Log changes to RBAC-related models
        if sender in rbac_models:
            logger.info(f"RBAC change: {sender.__name__} deleted - {instance}")
            
    except Exception as e:
        logger.error(f"Error logging RBAC change on delete: {e}")


@receiver(m2m_changed)
def log_rbac_changes_on_m2m_change(sender, instance, action, **kwargs):
    """Log RBAC M2M changes for debugging (no cache clearing needed)"""
    try:
        rbac_models = get_rbac_models()
        
        # Log M2M relationship changes
        if sender in rbac_models or instance.__class__ in rbac_models:
            if action in ['post_add', 'post_remove', 'post_clear']:
                logger.info(f"RBAC change: M2M {action} on {instance.__class__.__name__} - {instance}")
                
    except Exception as e:
        logger.error(f"Error logging RBAC M2M change: {e}")