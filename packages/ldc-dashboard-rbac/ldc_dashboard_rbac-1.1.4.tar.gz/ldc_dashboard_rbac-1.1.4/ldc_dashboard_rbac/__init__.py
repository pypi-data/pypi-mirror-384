"""
Django Feature RBAC - Group-based Role-Based Access Control with Onboarding - Simplified Version
"""

# Core permission functions
from ldc_dashboard_rbac.permissions import (
    user_has_feature_permission,
    get_user_features,
    is_superadmin_user,
    is_admin_user,
    get_rbac_config,
)

# Decorators for Django views
from ldc_dashboard_rbac.decorators import (
    feature_required,
    admin_required,
    superadmin_required,
)

# DRF permissions
try:
    from ldc_dashboard_rbac.drf_permissions import (
        HasFeaturePermission,
        IsFeatureAdmin,
        IsSuperAdmin,
        DynamicFeaturePermission,
    )
except ImportError:
    # DRF not installed
    pass

# Onboarding views - lazy import to avoid AppRegistryNotReady
def _lazy_import_onboarding():
    from ldc_dashboard_rbac.onboarding import (
        RegistrationView,
        AdminRegistrationView,
        ResetPasswordView,
        SetPasswordView,
        UserApprovalView,
    )
    return (RegistrationView, AdminRegistrationView, ResetPasswordView, SetPasswordView, UserApprovalView)

# Abstract models - lazy import to avoid AppRegistryNotReady
def _lazy_import_models():
    from ldc_dashboard_rbac.models import (
        AbstractFeature,
        AbstractDashboardUser,
        AbstractGroup,
        AbstractUserGroupMembership,
        AbstractGroupFeaturePermission,
        AbstractPasswordResetToken,
        AbstractUserGroup,
    )
    return (AbstractFeature, AbstractDashboardUser, AbstractGroup, AbstractUserGroupMembership,
            AbstractGroupFeaturePermission, AbstractPasswordResetToken, AbstractUserGroup)

# Utility functions - lazy import to avoid AppRegistryNotReady
def _lazy_import_utils():
    from ldc_dashboard_rbac.utils import (
        send_email,
        sync_features_from_urls,
        get_user_permission_summary,
        validate_rbac_configuration,
        export_rbac_configuration,
        import_rbac_configuration,
    )
    return (send_email, sync_features_from_urls, get_user_permission_summary,
            validate_rbac_configuration, export_rbac_configuration, import_rbac_configuration)

from ldc_dashboard_rbac.context_processors import rbac_permissions

# Make lazy imports available via __getattr__ (Python 3.7+)
def __getattr__(name):
    """Lazy load modules to avoid AppRegistryNotReady errors"""
    
    # Onboarding views
    if name in ('RegistrationView', 'AdminRegistrationView', 'ResetPasswordView', 
                'SetPasswordView', 'UserApprovalView'):
        views = _lazy_import_onboarding()
        view_map = {
            'RegistrationView': views[0],
            'AdminRegistrationView': views[1],
            'ResetPasswordView': views[2],
            'SetPasswordView': views[3],
            'UserApprovalView': views[4],
        }
        return view_map[name]
    
    # Abstract models
    if name in ('AbstractFeature', 'AbstractDashboardUser', 'AbstractGroup',
                'AbstractUserGroupMembership', 'AbstractGroupFeaturePermission',
                'AbstractPasswordResetToken', 'AbstractUserGroup'):
        models = _lazy_import_models()
        model_map = {
            'AbstractFeature': models[0],
            'AbstractDashboardUser': models[1],
            'AbstractGroup': models[2],
            'AbstractUserGroupMembership': models[3],
            'AbstractGroupFeaturePermission': models[4],
            'AbstractPasswordResetToken': models[5],
            'AbstractUserGroup': models[6],
        }
        return model_map[name]
    
    # Utility functions
    if name in ('send_email', 'sync_features_from_urls', 'get_user_permission_summary',
                'validate_rbac_configuration', 'export_rbac_configuration', 'import_rbac_configuration'):
        utils = _lazy_import_utils()
        util_map = {
            'send_email': utils[0],
            'sync_features_from_urls': utils[1],
            'get_user_permission_summary': utils[2],
            'validate_rbac_configuration': utils[3],
            'export_rbac_configuration': utils[4],
            'import_rbac_configuration': utils[5],
        }
        return util_map[name]
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__version__ = '1.1.4'
__author__ = 'Nishant Baruah'
__email__ = 'nishant.baruah@lendenclub.com'

# Default Django app configuration
default_app_config = 'ldc_dashboard_rbac.apps.LdcDashboardRbacConfig'

# Backward compatibility - alias for the old name
feature_permission_required = feature_required

__all__ = [
    # Permission functions
    'user_has_feature_permission',
    'get_user_features', 
    'is_superadmin_user',
    'is_admin_user',
    'get_rbac_config',
    
    # Decorators
    'feature_required',
    'feature_permission_required',  # Backward compatibility alias
    'admin_required',
    'superadmin_required',
    
    # DRF permissions (if available)
    'HasFeaturePermission',
    'IsFeatureAdmin',
    'IsSuperAdmin',
    'DynamicFeaturePermission',
    
    # Onboarding views (lazy loaded)
    'RegistrationView',
    'AdminRegistrationView',
    'ResetPasswordView',
    'SetPasswordView',
    'UserApprovalView',
    
    # Abstract models (lazy loaded)
    'AbstractFeature',
    'AbstractDashboardUser',
    'AbstractGroup',
    'AbstractUserGroupMembership',
    'AbstractGroupFeaturePermission',
    'AbstractPasswordResetToken',
    'AbstractUserGroup',
    
    # Utility functions (lazy loaded)
    'send_email',
    'sync_features_from_urls',
    'get_user_permission_summary',
    'validate_rbac_configuration',
    'export_rbac_configuration',
    'import_rbac_configuration',
    'rbac_permissions',
]