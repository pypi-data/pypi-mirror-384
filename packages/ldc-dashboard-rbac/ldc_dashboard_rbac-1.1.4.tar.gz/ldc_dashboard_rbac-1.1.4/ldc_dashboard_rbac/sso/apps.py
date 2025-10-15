# apps.py
from django.apps import AppConfig

class DashboardSsoConfig(AppConfig):
    name = 'ldc_dashboard_rbac.sso'  # Generic name
    verbose_name = 'Dashboard SSO'
    
    def ready(self):
        # Validate configuration at startup
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured
        
        sso_config = getattr(settings, 'DASHBOARD_SSO_CONFIG', {})
        required_settings = [
            'GOOGLE_OAUTH_CLIENT_ID',
            'GOOGLE_OAUTH_CLIENT_SECRET', 
            'SSO_POST_LOGIN_FUNCTION'
        ]
        
        missing = [key for key in required_settings if not sso_config.get(key)]
        if missing:
            raise ImproperlyConfigured(
                f"DASHBOARD_SSO_CONFIG missing required settings: {missing}"
            )