"""
Core permission checking logic for simplified RBAC system
"""
from typing import Any, Optional, Union
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

from ldc_dashboard_rbac.constants import (
    SettingsKeys, UserRoles, ErrorMessages, LogMessages
)

logger = logging.getLogger(__name__)


def get_rbac_config() -> dict:
    """Get RBAC configuration from Django settings"""
    config = getattr(settings, SettingsKeys.GROUP_RBAC, {})
    if not config:
        raise ImproperlyConfigured(ErrorMessages.GROUP_RBAC_MISSING)
    return config


def _get_model_with_validation(config_key: str, model_description: str):
    """Get a model from config with proper error handling"""
    config = get_rbac_config()
    model_path = config.get(config_key)
    
    if not model_path:
        example = config_key.split('_')[0].title()
        raise ImproperlyConfigured(
            ErrorMessages.REQUIRED_SETTING_MISSING.format(
                setting_key=config_key,
                description=model_description,
                example=example
            )
        )
    
    try:
        return apps.get_model(model_path)
    except Exception as e:
        raise ImproperlyConfigured(
            ErrorMessages.INVALID_MODEL_PATH.format(
                setting_key=config_key,
                model_path=model_path,
                error=e
            )
        )


def is_superadmin_user(user: Any) -> bool:
    """Check if user is superadmin"""
    if not user or getattr(user, 'is_anonymous', True):
        return False
    
    # Check if user has is_superadmin property
    if hasattr(user, 'is_superadmin'):
        return user.is_superadmin
    
    # Check role field
    if hasattr(user, 'role'):
        return user.role in UserRoles.SUPERADMIN_ROLES
    
    # Check using configured function
    try:
        config = get_rbac_config()
        superadmin_check = config.get(SettingsKeys.GroupRBAC.SUPER_ADMIN_CHECK)
        if superadmin_check and callable(superadmin_check):
            return superadmin_check(user)
    except Exception as e:
        logger.warning(f"Error checking superadmin status: {e}")
    
    return False


def is_admin_user(user: Any) -> bool:
    """Check if user is admin (includes superadmin)"""
    if not user or getattr(user, 'is_anonymous', True):
        return False
    
    # Check if user has is_admin property
    if hasattr(user, 'is_admin'):
        return user.is_admin
    
    # Check role field
    if hasattr(user, 'role'):
        return user.role in UserRoles.ADMIN_ROLES
    
    # Check using configured function
    try:
        config = get_rbac_config()
        admin_check = config.get(SettingsKeys.GroupRBAC.ADMIN_CHECK)
        if admin_check and callable(admin_check):
            return admin_check(user)
    except Exception as e:
        logger.warning(f"Error checking admin status: {e}")
    
    return False


def user_has_feature_permission(user: Any, feature_url_name: str) -> bool:
    """
    Check if user has permission for a feature - Simplified Version
    Only checks if user has access to the feature through group membership
    
    Args:
        user: User instance (any model)
        feature_url_name: URL name of the feature
    
    Returns:
        bool: True if user has permission
    """
    if not user or getattr(user, 'is_anonymous', True):
        return False
    
    # ✅ SUPERADMIN BYPASS: Always allow superadmin access
    if is_superadmin_user(user):
        logger.info(LogMessages.SUPERADMIN_ACCESS_GRANTED.format(user=user, feature_name=feature_url_name))
        return True
    
    # ✅ ADMIN BYPASS: Always allow admin access
    if is_admin_user(user):
        logger.info(LogMessages.ADMIN_ACCESS_GRANTED.format(user=user, feature_name=feature_url_name))
        return True
    
    try:
        # Get models with proper validation
        feature_model = _get_model_with_validation(SettingsKeys.GroupRBAC.FEATURE_MODEL, 'Feature')
        user_group_model = _get_model_with_validation(SettingsKeys.GroupRBAC.USER_GROUP_MODEL, 'UserGroupMembership')
        permission_model = _get_model_with_validation(SettingsKeys.GroupRBAC.PERMISSION_MODEL, 'GroupFeaturePermission')
        
        # Check if feature exists and is active
        try:
            feature = feature_model.objects.get(url_name=feature_url_name, is_active=True)
        except feature_model.DoesNotExist:
            logger.warning(LogMessages.FEATURE_NOT_FOUND_WARNING.format(feature_name=feature_url_name))
            return False
        
        # Get user's active groups
        user_groups = user_group_model.objects.filter(
            user=user,
            is_active=True,
            group__is_active=True
        ).values_list('group_id', flat=True)
        
        if not user_groups:
            return False
        
        # Check feature-level permissions - Simplified: just check if permission exists and is enabled
        has_permission = permission_model.objects.filter(
            group_id__in=user_groups,
            feature=feature,
            is_enabled=True
        ).exists()
        
        return has_permission
        
    except Exception as e:
        logger.error(f"Error checking permission for {user} on {feature_url_name}: {e}")
        return False


def get_user_features(user: Any) -> list:
    """Get all features accessible to the user - Simplified Version"""
    if not user or getattr(user, 'is_anonymous', True):
        return []
    
    # ✅ SUPERADMIN BYPASS: Return all active features for superadmin
    if is_superadmin_user(user):
        try:
            feature_model = _get_model_with_validation(SettingsKeys.GroupRBAC.FEATURE_MODEL, 'Feature')
            return list(feature_model.objects.filter(is_active=True).values_list('url_name', flat=True))
        except Exception as e:
            logger.error(f"Error getting superadmin features: {e}")
            return []
    
    # ✅ ADMIN BYPASS: Return all active features for admin
    if is_admin_user(user):
        try:
            feature_model = _get_model_with_validation(SettingsKeys.GroupRBAC.FEATURE_MODEL, 'Feature')
            return list(feature_model.objects.filter(is_active=True).values_list('url_name', flat=True))
        except Exception as e:
            logger.error(f"Error getting admin features: {e}")
            return []
    
    try:
        # Get models
        feature_model = _get_model_with_validation(SettingsKeys.GroupRBAC.FEATURE_MODEL, 'Feature')
        user_group_model = _get_model_with_validation(SettingsKeys.GroupRBAC.USER_GROUP_MODEL, 'UserGroupMembership')
        permission_model = _get_model_with_validation(SettingsKeys.GroupRBAC.PERMISSION_MODEL, 'GroupFeaturePermission')
        
        # Get user's active groups
        user_groups = user_group_model.objects.filter(
            user=user,
            is_active=True,
            group__is_active=True
        ).values_list('group_id', flat=True)
        
        if not user_groups:
            return []
        
        # Get features through group permissions - Simplified
        features = permission_model.objects.filter(
            group_id__in=user_groups,
            is_enabled=True,
            feature__is_active=True
        ).values_list('feature__url_name', flat=True)
        
        return list(features)
        
    except Exception as e:
        logger.error(f"Error getting user features: {e}")
        return []


def get_user_groups(user: Any) -> list:
    """Get all groups the user belongs to"""
    if not user or getattr(user, 'is_anonymous', True):
        return []
    
    try:
        user_group_model = _get_model_with_validation(SettingsKeys.GroupRBAC.USER_GROUP_MODEL, 'UserGroupMembership')
        group_model = _get_model_with_validation(SettingsKeys.GroupRBAC.GROUP_MODEL, 'Group')
        
        user_groups = user_group_model.objects.filter(
            user=user,
            is_active=True,
            group__is_active=True
        ).select_related('group')
        
        return [membership.group for membership in user_groups]
        
    except Exception as e:
        logger.error(f"Error getting user groups: {e}")
        return []


def validate_rbac_configuration() -> dict:
    """Validate RBAC configuration and return status"""
    status = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'config': {}
    }
    
    try:
        config = get_rbac_config()
        status['config'] = config
        
        # Check required settings
        required_settings = [
            SettingsKeys.GroupRBAC.USER_MODEL,
            SettingsKeys.GroupRBAC.FEATURE_MODEL,
            SettingsKeys.GroupRBAC.GROUP_MODEL,
            SettingsKeys.GroupRBAC.USER_GROUP_MODEL,
            SettingsKeys.GroupRBAC.PERMISSION_MODEL,
            SettingsKeys.GroupRBAC.USER_GETTER,
            SettingsKeys.GroupRBAC.SUPER_ADMIN_CHECK,
            SettingsKeys.GroupRBAC.ADMIN_CHECK,
        ]
        
        for setting in required_settings:
            if setting not in config:
                status['errors'].append(f"Missing required setting: {setting}")
                status['valid'] = False
            else:
                try:
                    if setting == SettingsKeys.GroupRBAC.USER_GETTER:
                        if not callable(config[setting]):
                            status['errors'].append(f"{setting} must be callable")
                            status['valid'] = False
                    else:
                        apps.get_model(config[setting])
                except Exception as e:
                    status['errors'].append(f"Invalid model path for {setting}: {e}")
                    status['valid'] = False
        
        # Check optional settings
        optional_settings = [
            SettingsKeys.GroupRBAC.PASSWORD_RESET_MODEL,
        ]
        
        for setting in optional_settings:
            if setting not in config:
                status['warnings'].append(f"Optional setting not configured: {setting}")
            else:
                try:
                    apps.get_model(config[setting])
                except Exception as e:
                    status['warnings'].append(f"Invalid model path for {setting}: {e}")
        
        if status['valid']:
            logger.info(LogMessages.CONFIG_VALIDATION_SUCCESS)
        
    except Exception as e:
        status['valid'] = False
        status['errors'].append(f"Configuration error: {e}")
    
    return status