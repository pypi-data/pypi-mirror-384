# c:\Users\Nishant Baruah\Desktop\rbac\dashboard_rbac\ldc_dashboard_rbac\context_processors.py

"""
Context processor for RBAC feature permissions in templates
Provides permission checking functionality in Django/Jinja templates
"""
import logging
from typing import Any, Dict

from ldc_dashboard_rbac.permissions import (
    get_rbac_config,
    user_has_feature_permission,
    is_superadmin_user,
    is_admin_user,
    get_user_features,
)
from ldc_dashboard_rbac.constants import SettingsKeys

logger = logging.getLogger(__name__)


class FeaturePermissionChecker:
    """
    Helper class to check feature permissions in templates
    Provides both callable and dict-like access
    """
    def __init__(self, user: Any):
        self.user = user
        self._is_superadmin = is_superadmin_user(user) if user else False
        self._is_admin = is_admin_user(user) if user else False
        self._accessible_features = None
    
    def __call__(self, feature_url_name: str) -> bool:
        """
        Allow calling as a function: has_feature('feature_name')
        
        Usage in templates:
            {% if has_feature('vendor_management') %}
                <a href="...">Vendor Management</a>
            {% endif %}
        """
        if not self.user or getattr(self.user, 'is_anonymous', True):
            return False
        
        # Superadmin and admin bypass
        if self._is_superadmin or self._is_admin:
            return True
        
        return user_has_feature_permission(self.user, feature_url_name)
    
    def __getitem__(self, feature_url_name: str) -> bool:
        """
        Allow dict-like access: has_feature['feature_name']
        
        Usage in templates:
            {% if has_feature['vendor_management'] %}
                <a href="...">Vendor Management</a>
            {% endif %}
        """
        return self(feature_url_name)
    
    @property
    def accessible_features(self) -> list:
        """
        Get list of all accessible features for the user
        Cached to avoid multiple DB queries
        
        Usage in templates:
            {% for feature in has_feature.accessible_features %}
                {{ feature }}
            {% endfor %}
        """
        if self._accessible_features is None:
            if not self.user or getattr(self.user, 'is_anonymous', True):
                self._accessible_features = []
            else:
                self._accessible_features = get_user_features(self.user)
        return self._accessible_features
    
    @property
    def is_superadmin(self) -> bool:
        """
        Check if user is superadmin
        
        Usage in templates:
            {% if has_feature.is_superadmin %}
                <a href="/admin">Admin Panel</a>
            {% endif %}
        """
        return self._is_superadmin
    
    @property
    def is_admin(self) -> bool:
        """
        Check if user is admin (includes superadmin)
        
        Usage in templates:
            {% if has_feature.is_admin %}
                <a href="/settings">Settings</a>
            {% endif %}
        """
        return self._is_admin or self._is_superadmin
    
    def any(self, *feature_url_names: str) -> bool:
        """
        Check if user has access to ANY of the given features
        
        Usage in templates:
            {% if has_feature.any('vendor_management', 'customer_management') %}
                <div>Management Section</div>
            {% endif %}
        """
        if not self.user or getattr(self.user, 'is_anonymous', True):
            return False
        
        if self._is_superadmin or self._is_admin:
            return True
        
        return any(self(feature) for feature in feature_url_names)
    
    def all(self, *feature_url_names: str) -> bool:
        """
        Check if user has access to ALL of the given features
        
        Usage in templates:
            {% if has_feature.all('vendor_read', 'vendor_write') %}
                <button>Edit Vendor</button>
            {% endif %}
        """
        if not self.user or getattr(self.user, 'is_anonymous', True):
            return False
        
        if self._is_superadmin or self._is_admin:
            return True
        
        return all(self(feature) for feature in feature_url_names)


def rbac_permissions(request) -> Dict[str, Any]:
    """
    Context processor to provide RBAC permission checking in templates
    
    Add this to your TEMPLATES['OPTIONS']['context_processors'] in settings.py:
        'ldc_dashboard_rbac.context_processors.rbac_permissions'
    
    Provides the following in templates:
        - has_feature: Function/dict to check feature permissions
        - user_features: List of accessible feature URL names
        - is_superadmin: Boolean indicating if user is superadmin
        - is_admin: Boolean indicating if user is admin
    
    Usage Examples in Templates:
    
        1. Basic feature check:
            {% if has_feature('vendor_management') %}
                <a href="/vendors">Vendors</a>
            {% endif %}
        
        2. Dict-style access:
            {% if has_feature['customer_management'] %}
                <a href="/customers">Customers</a>
            {% endif %}
        
        3. Check multiple features (any):
            {% if has_feature.any('vendor_management', 'customer_management') %}
                <div>Management Section</div>
            {% endif %}
        
        4. Check multiple features (all):
            {% if has_feature.all('vendor_read', 'vendor_write') %}
                <button>Edit Vendor</button>
            {% endif %}
        
        5. Admin/Superadmin check:
            {% if has_feature.is_superadmin %}
                <a href="/admin">Admin Panel</a>
            {% endif %}
        
        6. List all accessible features:
            {% for feature in has_feature.accessible_features %}
                <li>{{ feature }}</li>
            {% endfor %}
    """
    user = None
    
    try:
        # Get user using configured getter
        config = get_rbac_config()
        user_getter = config.get(SettingsKeys.GroupRBAC.USER_GETTER)
        
        if user_getter and callable(user_getter):
            user = user_getter(request)
        else:
            logger.warning("USER_GETTER not configured or not callable in RBAC context processor")
    
    except Exception as e:
        logger.error(f"Error getting user in RBAC context processor: {e}")
    
    # Create permission checker instance
    permission_checker = FeaturePermissionChecker(user)
    
    return {
        'has_feature': permission_checker,
        'user_features': permission_checker.accessible_features,
        'is_superadmin': permission_checker.is_superadmin,
        'is_admin': permission_checker.is_admin,
    }