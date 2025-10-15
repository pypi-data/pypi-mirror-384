"""
Utility functions for group RBAC with email configuration
"""
from django.core.cache import cache
from django.conf import settings
from django.apps import apps
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from ldc_dashboard_rbac.permissions import clear_user_permissions_cache
from ldc_dashboard_rbac.constants import (
    SettingsKeys, UserRoles, PermissionLevels, LogMessages, 
    HTTPStatus, TemplatePaths, ValidationRules
)
import logging

logger = logging.getLogger(__name__)


def send_email(to_email, subject, template, context=None, from_email=None):
    """
    Send email using configured email service
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        template: Template path for email content
        context: Context variables for template
        from_email: Sender email (optional, uses default if not provided)
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        if context is None:
            context = {}
        
        # Get email configuration
        email_config = getattr(settings, SettingsKeys.RBAC_EMAIL_CONFIG, {})
        
        # Use configured from_email or default
        if not from_email:
            from_email = email_config.get(SettingsKeys.EmailConfig.FROM_EMAIL, 
                                        getattr(settings, SettingsKeys.DEFAULT_FROM_EMAIL))
        
        # Render email content
        html_content = render_to_string(template, context)
        
        # Use configured email backend or default
        email_backend = email_config.get(SettingsKeys.EmailConfig.EMAIL_BACKEND)
        if email_backend:
            # Temporarily set email backend
            original_backend = settings.EMAIL_BACKEND
            settings.EMAIL_BACKEND = email_backend
            
            try:
                send_mail(
                    subject=subject,
                    message='',  # Plain text version (optional)
                    html_message=html_content,
                    from_email=from_email,
                    recipient_list=[to_email],
                    fail_silently=False
                )
            finally:
                # Restore original backend
                settings.EMAIL_BACKEND = original_backend
        else:
            # Use default Django email
            send_mail(
                subject=subject,
                message='',  # Plain text version (optional)
                html_message=html_content,
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False
            )
        
        logger.info(LogMessages.EMAIL_SENT_SUCCESS.format(email=to_email))
        return True
        
    except Exception as e:
        logger.error(LogMessages.EMAIL_SEND_ERROR.format(email=to_email, error=e))
        return False


def sync_features_from_urls():
    """
    Synchronize features from Django URL patterns
    
    This function scans all URL patterns and creates Feature objects
    for any named URLs that don't already exist.
    """
    from django.urls import get_resolver
    # Use lazy import to avoid circular imports
    from ldc_dashboard_rbac.permissions import get_models
    
    try:
        User, Feature, Group, UserGroup, GroupFeaturePermission = get_models()
        
        resolver = get_resolver()
        created_count = 0
        
        def extract_url_names(url_patterns, namespace=''):
            """Recursively extract URL names from patterns"""
            names = []
            for pattern in url_patterns:
                if hasattr(pattern, 'name') and pattern.name:
                    full_name = f"{namespace}:{pattern.name}" if namespace else pattern.name
                    names.append(full_name)
                elif hasattr(pattern, 'url_patterns'):
                    # Handle included URL patterns
                    pattern_namespace = getattr(pattern, 'namespace', '')
                    if pattern_namespace:
                        pattern_namespace = f"{namespace}:{pattern_namespace}" if namespace else pattern_namespace
                    names.extend(extract_url_names(pattern.url_patterns, pattern_namespace))
            return names
        
        url_names = extract_url_names(resolver.url_patterns)
        
        for url_name in url_names:
            if not Feature.objects.filter(url_name=url_name).exists():
                # Create a human-readable name from URL name
                display_name = url_name.replace('_', ' ').replace(':', ' - ').title()
                
                Feature.objects.create(
                    name=display_name,
                    url_name=url_name,
                    description=f"Auto-generated feature for {url_name}",
                    is_active=False  # Start as inactive for security
                )
                created_count += 1
                logger.info(LogMessages.FEATURE_CREATED.format(display_name=display_name, url_name=url_name))
        
        logger.info(LogMessages.FEATURE_SYNC_COMPLETED.format(count=created_count))
        return created_count
        
    except Exception as e:
        logger.error(LogMessages.FEATURE_SYNC_ERROR.format(error=e))
        raise


def clear_all_permission_cache():
    """Clear all RBAC permission cache"""
    try:
        # This is a simplified approach
        # In production, consider using cache tagging for more efficient clearing
        cache.clear()
        logger.info("All RBAC permission cache cleared")
    except Exception as e:
        logger.error(f"Error clearing permission cache: {e}")


def get_user_permission_summary(user):
    """
    Get a summary of user's permissions with role-based access
    
    Returns a dictionary with user's groups, features, and permission levels
    """
    # Use lazy imports to avoid circular imports
    from ldc_dashboard_rbac.permissions import get_models, get_user_features, get_user_groups, is_superadmin_user, is_admin_user
    
    try:
        User, Feature, Group, UserGroupMembership, GroupFeaturePermission, PasswordResetToken = get_models()
        
        if not user or getattr(user, 'is_anonymous', True):
            return {
                'groups': [],
                'features': [],
                'total_groups': 0,
                'total_features': 0,
                'permission_levels': {},
                'role': 'anonymous',
                'is_superadmin': False,
                'is_admin': False
            }
        
        # Check user role
        is_superadmin = is_superadmin_user(user)
        is_admin = is_admin_user(user)
        user_role = getattr(user, 'role', UserRoles.USER)
        
        groups = get_user_groups(user)
        features = get_user_features(user)
        
        # Get permission levels for each feature
        permission_levels = {}
        if not is_superadmin and not is_admin:
            # Only check feature-level permissions for regular users
            permissions = GroupFeaturePermission.objects.filter(
                group__user_memberships__user=user,
                group__user_memberships__is_active=True,
                group__is_active=True,
                is_enabled=True
            ).select_related('feature')
            
            for perm in permissions:
                feature_name = perm.feature.url_name
                current_level = permission_levels.get(feature_name, PermissionLevels.READ)
                
                # Keep the highest permission level
                if PermissionLevels.WEIGHTS.get(perm.permission_level, 1) > PermissionLevels.WEIGHTS.get(current_level, 1):
                    permission_levels[feature_name] = perm.permission_level
        else:
            # Superadmin and admin have all permissions
            for feature in features:
                permission_levels[feature.url_name] = PermissionLevels.ADMIN
        
        return {
            'groups': list(groups.values('id', 'group_name', 'description')),
            'features': list(features.values('id', 'name', 'url_name', 'category')),
            'total_groups': groups.count(),
            'total_features': features.count(),
            'permission_levels': permission_levels,
            'role': user_role,
            'is_superadmin': is_superadmin,
            'is_admin': is_admin
        }
        
    except Exception as e:
        logger.error(f"Error getting user permission summary: {e}")
        return {
            'groups': [],
            'features': [],
            'total_groups': 0,
            'total_features': 0,
            'permission_levels': {},
            'role': 'unknown',
            'is_superadmin': False,
            'is_admin': False
        }


def validate_rbac_configuration():
    """
    Validate RBAC configuration and return any issues
    
    Returns a list of configuration issues or empty list if valid
    """
    issues = []
    
    try:
        config = getattr(settings, SettingsKeys.GROUP_RBAC, {})
        
        # Check required configuration
        if not config.get(SettingsKeys.GroupRBAC.USER_GETTER):
            issues.append(f"{SettingsKeys.GROUP_RBAC}['{SettingsKeys.GroupRBAC.USER_GETTER}'] is not configured")
        
        if not config.get(SettingsKeys.GroupRBAC.SUPER_ADMIN_CHECK):
            issues.append(f"{SettingsKeys.GROUP_RBAC}['{SettingsKeys.GroupRBAC.SUPER_ADMIN_CHECK}'] is not configured")
        
        if not config.get(SettingsKeys.GroupRBAC.ADMIN_CHECK):
            issues.append(f"{SettingsKeys.GROUP_RBAC}['{SettingsKeys.GroupRBAC.ADMIN_CHECK}'] is not configured")
        
        # Check if models exist
        try:
            from ldc_dashboard_rbac.permissions import get_models
            get_models()
        except Exception as e:
            issues.append(f"Error loading RBAC models: {e}")
        
        # Check if user getter function is callable
        user_getter = config.get(SettingsKeys.GroupRBAC.USER_GETTER)
        if user_getter and not callable(user_getter):
            issues.append(f"{SettingsKeys.GROUP_RBAC}['{SettingsKeys.GroupRBAC.USER_GETTER}'] is not callable")
        
        # Check if admin check functions are callable
        super_admin_check = config.get(SettingsKeys.GroupRBAC.SUPER_ADMIN_CHECK)
        if super_admin_check and not callable(super_admin_check):
            issues.append(f"{SettingsKeys.GROUP_RBAC}['{SettingsKeys.GroupRBAC.SUPER_ADMIN_CHECK}'] is not callable")
        
        admin_check = config.get(SettingsKeys.GroupRBAC.ADMIN_CHECK)
        if admin_check and not callable(admin_check):
            issues.append(f"{SettingsKeys.GROUP_RBAC}['{SettingsKeys.GroupRBAC.ADMIN_CHECK}'] is not callable")
        
    except Exception as e:
        issues.append(f"Error validating RBAC configuration: {e}")
    
    return issues


def export_rbac_configuration():
    """
    Export current RBAC configuration for backup or migration
    
    Returns a dictionary with all groups, features, and permissions
    """
    from ldc_dashboard_rbac.permissions import get_models
    
    try:
        User, Feature, Group, UserGroupMembership, GroupFeaturePermission, PasswordResetToken = get_models()
        
        # Export features
        features = list(Feature.objects.values(
            'name', 'url_name', 'description', 'category', 'is_active'
        ))
        
        # Export groups
        groups = list(Group.objects.values(
            'group_name', 'description', 'permission_level', 'is_active'
        ))
        
        # Export permissions
        permissions = list(GroupFeaturePermission.objects.select_related(
            'group', 'feature'
        ).values(
            'group__group_name', 'feature__url_name', 'permission_level', 'is_enabled'
        ))
        
        # Export user-group memberships
        user_groups = list(UserGroupMembership.objects.select_related(
            'user', 'group'
        ).values(
            'user__email', 'group__group_name', 'is_active'
        ))
        
        # Export users (without passwords)
        users = list(User.objects.values(
            'name', 'email', 'is_active', 'role'
        ))
        
        return {
            'features': features,
            'groups': groups,
            'permissions': permissions,
            'user_groups': user_groups,
            'users': users,
            'export_timestamp': timezone.now().isoformat(),
            'version': '2.0'
        }
        
    except Exception as e:
        logger.error(f"Error exporting RBAC configuration: {e}")
        raise


def import_rbac_configuration(config_data):
    """
    Import RBAC configuration from exported data
    
    Args:
        config_data: Dictionary from export_rbac_configuration()
        
    Returns:
        Dictionary with import statistics
    """
    from ldc_dashboard_rbac.permissions import get_models
    from django.db import transaction
    
    try:
        User, Feature, Group, UserGroupMembership, GroupFeaturePermission, PasswordResetToken = get_models()
        
        stats = {
            'features_created': 0,
            'groups_created': 0,
            'permissions_created': 0,
            'user_groups_created': 0,
            'users_created': 0,
            'errors': []
        }
        
        with transaction.atomic():
            # Import features
            for feature_data in config_data.get('features', []):
                feature, created = Feature.objects.get_or_create(
                    url_name=feature_data['url_name'],
                    defaults=feature_data
                )
                if created:
                    stats['features_created'] += 1
            
            # Import groups
            for group_data in config_data.get('groups', []):
                group, created = Group.objects.get_or_create(
                    group_name=group_data['group_name'],
                    defaults=group_data
                )
                if created:
                    stats['groups_created'] += 1
            
            # Import users (without passwords - they'll need to reset)
            for user_data in config_data.get('users', []):
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'name': user_data['name'],
                        'is_active': False,  # Require password reset
                        'role': user_data['role']
                    }
                )
                if created:
                    stats['users_created'] += 1
            
            # Import permissions
            for perm_data in config_data.get('permissions', []):
                try:
                    group = Group.objects.get(group_name=perm_data['group__group_name'])
                    feature = Feature.objects.get(url_name=perm_data['feature__url_name'])
                    
                    permission, created = GroupFeaturePermission.objects.get_or_create(
                        group=group,
                        feature=feature,
                        defaults={
                            'permission_level': perm_data['permission_level'],
                            'is_enabled': perm_data['is_enabled']
                        }
                    )
                    if created:
                        stats['permissions_created'] += 1
                        
                except (Group.DoesNotExist, Feature.DoesNotExist) as e:
                    stats['errors'].append(f"Permission import error: {e}")
            
            # Import user-group memberships
            for ug_data in config_data.get('user_groups', []):
                try:
                    user = User.objects.get(email=ug_data['user__email'])
                    group = Group.objects.get(group_name=ug_data['group__group_name'])
                    
                    user_group, created = UserGroupMembership.objects.get_or_create(
                        user=user,
                        group=group,
                        defaults={
                            'is_active': ug_data['is_active']
                        }
                    )
                    if created:
                        stats['user_groups_created'] += 1
                        
                except (User.DoesNotExist, Group.DoesNotExist) as e:
                    stats['errors'].append(f"User-group import error: {e}")
        
        logger.info(f"RBAC configuration imported successfully: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error importing RBAC configuration: {e}")
        raise