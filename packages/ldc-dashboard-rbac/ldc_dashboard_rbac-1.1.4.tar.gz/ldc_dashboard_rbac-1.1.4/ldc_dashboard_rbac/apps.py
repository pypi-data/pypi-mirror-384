from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)


class LdcDashboardRbacConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ldc_dashboard_rbac'
    verbose_name = 'LDC Dashboard RBAC'
    
    def ready(self):
        """Import signals and validate configuration when Django starts"""
        try:
            # Import signals
            from ldc_dashboard_rbac import signals
            logger.info("RBAC signals loaded")
            
            # Validate configuration on startup
            self._validate_rbac_configuration()
            
        except Exception as e:
            logger.error(f"Error during RBAC initialization: {e}")
    
    def _validate_rbac_configuration(self):
        """Validate RBAC configuration and raise errors for missing required settings"""
        from django.conf import settings
        from django.apps import apps
        
        # Get configuration
        config = getattr(settings, 'GROUP_RBAC', {})
        
        if not config:
            raise ImproperlyConfigured(
                "GROUP_RBAC configuration is missing from Django settings. "
                "Please add GROUP_RBAC dictionary to your settings.py"
            )
        
        # Check required settings
        required_settings = [
            ('USER_MODEL', 'Path to your user model (e.g., "myapp.User")'),
            ('USER_GETTER', 'Function to get user from request'),
        ]
        
        missing_settings = []
        for setting_key, description in required_settings:
            if not config.get(setting_key):
                missing_settings.append(f"  - {setting_key}: {description}")
        
        if missing_settings:
            raise ImproperlyConfigured(
                f"Missing required GROUP_RBAC settings:\n" + 
                "\n".join(missing_settings) +
                "\n\nExample configuration:\n"
                "GROUP_RBAC = {\n"
                "    'USER_MODEL': 'myapp.User',\n"
                "    'USER_GETTER': lambda request: getattr(request, 'user', None),\n"
                "    'FEATURE_MODEL': 'myapp.Feature',  # optional\n"
                "    'GROUP_MODEL': 'myapp.Group',  # optional\n"
                "}\n"
            )
        
        # Validate that USER_GETTER is callable
        user_getter = config.get('USER_GETTER')
        if user_getter and not callable(user_getter):
            raise ImproperlyConfigured(
                f"GROUP_RBAC['USER_GETTER'] must be a callable function, got {type(user_getter)}"
            )
        
        # Validate model paths exist (only check USER_MODEL as it's required)
        try:
            user_model_path = config.get('USER_MODEL')
            apps.get_model(user_model_path)
        except Exception as e:
            raise ImproperlyConfigured(
                f"GROUP_RBAC['USER_MODEL'] = '{user_model_path}' is invalid: {e}"
            )
        
        # Warn about optional settings with defaults
        optional_settings = {
            'FEATURE_MODEL': 'myapp.Feature',
            'GROUP_MODEL': 'myapp.Group', 
            'USER_GROUP_MODEL': 'myapp.UserGroupMembership',
            'GROUP_FEATURE_PERMISSION_MODEL': 'myapp.GroupFeaturePermission',
            'PASSWORD_RESET_MODEL': 'myapp.PasswordResetToken',
        }
        
        for setting_key, example in optional_settings.items():
            if not config.get(setting_key):
                logger.warning(
                    f"GROUP_RBAC['{setting_key}'] not configured. "
                    f"Using default which may not exist. "
                    f"Consider setting it to '{example}'"
                )
        
        logger.info("RBAC configuration validation completed successfully")