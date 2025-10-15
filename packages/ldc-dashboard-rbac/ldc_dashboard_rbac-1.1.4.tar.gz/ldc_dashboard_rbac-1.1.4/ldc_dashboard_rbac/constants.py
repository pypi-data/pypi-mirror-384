"""
Constants for the LDC Dashboard RBAC package - Simplified Version
"""

# User Roles
class UserRoles:
    USER = 'user'
    ADMIN = 'admin'
    SUPERADMIN = 'superadmin'
    
    # Legacy role names for backward compatibility
    SUPER_ADMIN = 'super_admin'
    
    # All role choices for Django model
    CHOICES = [
        (USER, 'User'),
        (ADMIN, 'Admin'),
        (SUPERADMIN, 'Super Admin'),
    ]
    
    # Admin roles (includes superadmin)
    ADMIN_ROLES = [ADMIN, SUPERADMIN, SUPER_ADMIN]
    
    # Superadmin roles (different naming conventions)
    SUPERADMIN_ROLES = [SUPERADMIN, SUPER_ADMIN]


# Django Settings Keys
class SettingsKeys:
    # Main RBAC configuration
    GROUP_RBAC = 'GROUP_RBAC'
    RBAC_EMAIL_CONFIG = 'RBAC_EMAIL_CONFIG'
    SITE_URL = 'SITE_URL'
    DEFAULT_FROM_EMAIL = 'DEFAULT_FROM_EMAIL'
    
    # RBAC configuration sub-keys
    class GroupRBAC:
        USER_MODEL = 'USER_MODEL'
        USER_GETTER = 'USER_GETTER'
        SUPER_ADMIN_CHECK = 'SUPER_ADMIN_CHECK'
        ADMIN_CHECK = 'ADMIN_CHECK'
        FEATURE_MODEL = 'FEATURE_MODEL'
        GROUP_MODEL = 'GROUP_MODEL'
        USER_GROUP_MODEL = 'USER_GROUP_MODEL'
        PERMISSION_MODEL = 'PERMISSION_MODEL'
        GROUP_FEATURE_PERMISSION_MODEL = 'GROUP_FEATURE_PERMISSION_MODEL'  # Legacy key
        PASSWORD_RESET_MODEL = 'PASSWORD_RESET_MODEL'
    
    # Email configuration sub-keys
    class EmailConfig:
        FROM_EMAIL = 'FROM_EMAIL'
        EMAIL_BACKEND = 'EMAIL_BACKEND'


# Default Model Paths (to be avoided, but kept for backward compatibility)
class DefaultModelPaths:
    USER = 'dashboard.DashboardUser'
    FEATURE = 'dashboard.Feature'
    GROUP = 'dashboard.Group'
    USER_GROUP = 'dashboard.UserGroupMembership'
    USER_GROUP_LEGACY = 'dashboard.UserGroup'  # Legacy naming
    PERMISSION = 'dashboard.GroupFeaturePermission'
    PASSWORD_RESET = 'dashboard.PasswordResetToken'


# Model Field Lengths
class FieldLengths:
    # Feature model
    FEATURE_NAME_MAX_LENGTH = 100
    FEATURE_URL_NAME_MAX_LENGTH = 100
    FEATURE_CATEGORY_MAX_LENGTH = 50
    
    # User model
    USER_NAME_MAX_LENGTH = 150
    USER_PASSWORD_MAX_LENGTH = 128
    USER_ROLE_MAX_LENGTH = 20
    
    # Group model
    GROUP_NAME_MAX_LENGTH = 100


# HTTP Status Codes
class HTTPStatus:
    OK = 200
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


# Template Paths
class TemplatePaths:
    # Permission denied templates
    PERMISSION_DENIED = 'ldc_dashboard_rbac/permission_denied.html'
    
    # Onboarding templates
    ONBOARDING_RESPONSE = 'ldc_dashboard_rbac/onboarding_response.html'
    REGISTRATION = 'ldc_dashboard_rbac/registration.html'
    ADMIN_REGISTRATION = 'ldc_dashboard_rbac/admin_registration.html'
    RESET_PASSWORD = 'ldc_dashboard_rbac/reset_password.html'
    SET_PASSWORD = 'ldc_dashboard_rbac/set_password.html'
    INVALID_TOKEN = 'ldc_dashboard_rbac/invalid_token.html'
    USER_APPROVAL = 'ldc_dashboard_rbac/user_approval.html'
    
    # Email templates
    class Email:
        ADMIN_REGISTRATION_NOTIFICATION = 'ldc_dashboard_rbac/emails/admin_registration_notification.html'
        PASSWORD_SETUP = 'ldc_dashboard_rbac/emails/password_setup.html'
        PASSWORD_RESET = 'ldc_dashboard_rbac/emails/password_reset.html'
        ACCOUNT_APPROVED = 'ldc_dashboard_rbac/emails/account_approved.html'
        ACCOUNT_REJECTED = 'ldc_dashboard_rbac/emails/account_rejected.html'


# API Detection Constants
class APIDetection:
    # HTTP Headers
    AJAX_HEADER = 'X-Requested-With'
    AJAX_VALUE = 'XMLHttpRequest'
    
    # Content Types
    JSON_CONTENT_TYPE = 'application/json'
    HTML_CONTENT_TYPE = 'text/html'
    API_JSON_CONTENT_TYPE = 'application/vnd.api+json'
    
    # User Agents (for API detection)
    API_USER_AGENTS = ['postman', 'insomnia', 'curl', 'python-requests', 'axios']
    
    # URL Patterns
    API_URL_PATTERN = '/api/'


# Error Messages
class ErrorMessages:
    # Configuration errors
    CONFIG_NOT_CONFIGURED = 'Access control not configured'
    GROUP_RBAC_MISSING = 'GROUP_RBAC configuration is missing from Django settings'
    USER_GETTER_NOT_CONFIGURED = 'USER_GETTER not configured in GROUP_RBAC settings'
    
    # Permission errors
    NO_FEATURE_PERMISSION = "You don't have permission to access this feature."
    NO_ADMIN_PERMISSION = "You don't have admin permission to access this feature."
    NO_SUPERADMIN_PERMISSION = "You don't have superadmin permission to access this feature."
    
    # Feature errors
    FEATURE_NOT_FOUND = "Feature '{feature_name}' not found or inactive"
    
    # Model validation errors
    REQUIRED_SETTING_MISSING = "GROUP_RBAC['{setting_key}'] is required but not configured. Please set it to your {description} model path (e.g., 'myapp.{example}')"
    INVALID_MODEL_PATH = "GROUP_RBAC['{setting_key}'] = '{model_path}' is invalid: {error}"
    USER_GETTER_NOT_CALLABLE = "GROUP_RBAC['USER_GETTER'] must be a callable function, got {type_name}"


# Default Values
class Defaults:
    # Model field defaults
    FEATURE_ACTIVE = True
    USER_ACTIVE = False  # Requires admin approval
    GROUP_ACTIVE = True
    MEMBERSHIP_ACTIVE = True
    PERMISSION_ENABLED = True
    TOKEN_USED = False
    
    # Permission defaults
    DEFAULT_USER_ROLE = UserRoles.USER
    
    # Pagination and limits
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


# Log Messages
class LogMessages:
    # Access granted messages
    SUPERADMIN_ACCESS_GRANTED = "Superadmin {user} granted access to {feature_name}"
    ADMIN_ACCESS_GRANTED = "Admin {user} granted access to {feature_name}"
    
    # Access denied messages
    FEATURE_NOT_FOUND_WARNING = "Feature '{feature_name}' not found or inactive"
    
    # Configuration messages
    RBAC_SIGNALS_LOADED = "RBAC signals loaded"
    CONFIG_VALIDATION_SUCCESS = "RBAC configuration validation completed successfully"
    CONFIG_WARNING = "GROUP_RBAC['{setting_key}'] not configured. Using default which may not exist. Consider setting it to '{example}'"
    
    # Email messages
    EMAIL_SENT_SUCCESS = "Email sent successfully to {email}"
    EMAIL_SEND_ERROR = "Error sending email to {email}: {error}"
    
    # Feature sync messages
    FEATURE_CREATED = "Created feature: {display_name} ({url_name})"
    FEATURE_SYNC_COMPLETED = "Feature sync completed. Created {count} new features."
    FEATURE_SYNC_ERROR = "Error syncing features from URLs: {error}"


# Validation Rules
class ValidationRules:
    # Email validation
    EMAIL_MAX_LENGTH = 254
    
    # Password validation
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    
    # Token validation
    TOKEN_EXPIRY_HOURS = 24
    
    # Name validation
    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 150


# UI Messages
class UIMessages:
    # Status indicators
    SET_INDICATOR = "✅ Set"
    NOT_SET_INDICATOR = "❌ Not set"
    NOT_SET_DEFAULT = "Not set"
    DJANGO_DEFAULT = "Django default"
    
    # User field names
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'


# Cache Keys (if caching is re-enabled in future)
class CacheKeys:
    USER_PERMISSIONS = 'rbac:user_permissions:{user_id}'
    USER_FEATURES = 'rbac:user_features:{user_id}'
    USER_GROUPS = 'rbac:user_groups:{user_id}'
    FEATURE_PERMISSIONS = 'rbac:feature_permissions:{feature_id}'
    
    # Cache timeouts (in seconds)
    DEFAULT_TIMEOUT = 300  # 5 minutes
    LONG_TIMEOUT = 3600    # 1 hour
    SHORT_TIMEOUT = 60     # 1 minute
