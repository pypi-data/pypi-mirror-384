"""
Constants for audit trail functionality
"""

class AuditTrailActionTypes:
    """Action types for audit trail entries"""
    
    # CRUD Operations
    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'
    
    # User Management
    LOGIN = 'login'
    LOGOUT = 'logout'
    REGISTER = 'register'
    APPROVE = 'approve'
    REJECT = 'reject'
    
    # Data Operations
    IMPORT = 'import'
    EXPORT = 'export'
    SYNC = 'sync'
    BACKUP = 'backup'
    RESTORE = 'restore'
    
    # System Operations
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    RESET = 'reset'
    MODIFY = 'modify'
    
    # Access Operations
    VIEW = 'view'
    ACCESS = 'access'
    DOWNLOAD = 'download'
    UPLOAD = 'upload'
    
    # Security Operations
    PERMISSION_GRANTED = 'permission_granted'
    PERMISSION_DENIED = 'permission_denied'
    PASSWORD_CHANGE = 'password_change'
    PASSWORD_RESET = 'password_reset'
    
    # All choices for Django model
    CHOICES = [
        (CREATE, 'Create'),
        (READ, 'Read'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
        (LOGIN, 'Login'),
        (LOGOUT, 'Logout'),
        (REGISTER, 'Register'),
        (APPROVE, 'Approve'),
        (REJECT, 'Reject'),
        (IMPORT, 'Import'),
        (EXPORT, 'Export'),
        (SYNC, 'Sync'),
        (BACKUP, 'Backup'),
        (RESTORE, 'Restore'),
        (ACTIVATE, 'Activate'),
        (DEACTIVATE, 'Deactivate'),
        (RESET, 'Reset'),
        (MODIFY, 'Modify'),
        (VIEW, 'View'),
        (ACCESS, 'Access'),
        (DOWNLOAD, 'Download'),
        (UPLOAD, 'Upload'),
        (PERMISSION_GRANTED, 'Permission Granted'),
        (PERMISSION_DENIED, 'Permission Denied'),
        (PASSWORD_CHANGE, 'Password Change'),
        (PASSWORD_RESET, 'Password Reset'),
    ]
    
    # Action categories
    CRUD_ACTIONS = [CREATE, READ, UPDATE, DELETE]
    AUTH_ACTIONS = [LOGIN, LOGOUT, REGISTER, APPROVE, REJECT]
    DATA_ACTIONS = [IMPORT, EXPORT, SYNC, BACKUP, RESTORE]
    SYSTEM_ACTIONS = [ACTIVATE, DEACTIVATE, RESET, MODIFY]
    ACCESS_ACTIONS = [VIEW, ACCESS, DOWNLOAD, UPLOAD]
    SECURITY_ACTIONS = [PERMISSION_GRANTED, PERMISSION_DENIED, PASSWORD_CHANGE, PASSWORD_RESET]


class AuditTrailEntityTypes:
    """Entity types for audit trail entries"""
    
    # User-related entities
    USER = 'user'
    DASHBOARD_USER = 'dashboard_user'
    USER_GROUP = 'user_group'
    GROUP = 'group'
    
    # Feature and Permission entities
    FEATURE = 'feature'
    PERMISSION = 'permission'
    ROLE = 'role'
    
    # System entities
    SYSTEM = 'system'
    CONFIGURATION = 'configuration'
    SETTING = 'setting'
    
    # Data entities
    DATA = 'data'
    FILE = 'file'
    REPORT = 'report'
    
    # Session entities
    SESSION = 'session'
    TOKEN = 'token'
    
    # Common choices (can be extended by projects)
    COMMON_CHOICES = [
        (USER, 'User'),
        (DASHBOARD_USER, 'Dashboard User'),
        (USER_GROUP, 'User Group'),
        (GROUP, 'Group'),
        (FEATURE, 'Feature'),
        (PERMISSION, 'Permission'),
        (ROLE, 'Role'),
        (SYSTEM, 'System'),
        (CONFIGURATION, 'Configuration'),
        (SETTING, 'Setting'),
        (DATA, 'Data'),
        (FILE, 'File'),
        (REPORT, 'Report'),
        (SESSION, 'Session'),
        (TOKEN, 'Token'),
    ]


class AuditTrailFieldLengths:
    """Field length constants for audit trail models"""
    
    USER_ROLE_MAX_LENGTH = 50
    ACTION_TYPE_MAX_LENGTH = 50
    ENTITY_TYPE_MAX_LENGTH = 50
    TRACE_ID_MAX_LENGTH = 100
    IP_ADDRESS_MAX_LENGTH = 45  # IPv6 support
    ERROR_MESSAGE_MAX_LENGTH = 1000


class AuditTrailConstants:
    """General constants for audit trail functionality"""
    
    # Default settings
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    DEFAULT_RETENTION_DAYS = 365  # 1 year
    
    # Performance settings
    BULK_CREATE_BATCH_SIZE = 1000
    ASYNC_QUEUE_NAME = 'audit_trail'
    
    # Security settings
    SENSITIVE_FIELDS = [
        'password', 'token', 'secret', 'key', 'credential',
        'api_key', 'access_token', 'refresh_token'
    ]
    
    # Default details keys
    class DetailsKeys:
        REQUEST_PATH = 'request_path'
        REQUEST_METHOD = 'request_method'
        RESPONSE_STATUS = 'response_status'
        EXECUTION_TIME = 'execution_time'
        CHANGES = 'changes'
        REASON = 'reason'
        METADATA = 'metadata'
        CONTEXT = 'context'
    
    # Error codes
    class ErrorCodes:
        AUDIT_CREATION_FAILED = 'AUDIT_001'
        INVALID_ACTION_TYPE = 'AUDIT_002'
        INVALID_ENTITY_TYPE = 'AUDIT_003'
        USER_NOT_FOUND = 'AUDIT_004'
        PERMISSION_DENIED = 'AUDIT_005'
        INVALID_DATA = 'AUDIT_006'
    
    # Log levels
    class LogLevels:
        INFO = 'info'
        WARNING = 'warning'
        ERROR = 'error'
        CRITICAL = 'critical'
        DEBUG = 'debug'


class AuditTrailSettings:
    """Settings keys for audit trail configuration"""
    
    # Main configuration key
    AUDIT_TRAIL_CONFIG = 'AUDIT_TRAIL_CONFIG'
    
    # Configuration sub-keys
    class Config:
        ENABLED = 'ENABLED'
        USER_MODEL = 'USER_MODEL'
        AUDIT_MODEL = 'AUDIT_MODEL'
        ASYNC_LOGGING = 'ASYNC_LOGGING'
        RETENTION_DAYS = 'RETENTION_DAYS'
        EXCLUDE_ACTIONS = 'EXCLUDE_ACTIONS'
        EXCLUDE_ENTITIES = 'EXCLUDE_ENTITIES'
        SENSITIVE_FIELDS = 'SENSITIVE_FIELDS'
        AUTO_TRACK_CHANGES = 'AUTO_TRACK_CHANGES'
        TRACK_IP_ADDRESS = 'TRACK_IP_ADDRESS'
        TRACK_USER_AGENT = 'TRACK_USER_AGENT'
        BULK_CREATE_BATCH_SIZE = 'BULK_CREATE_BATCH_SIZE'


class MessageCodes:
    """Message codes for audit trail responses"""
    
    # Success codes
    SUCCESS = 'AUDIT_SUCCESS'
    AUDIT_CREATED = 'AUDIT_CREATED'
    AUDIT_RETRIEVED = 'AUDIT_RETRIEVED'
    
    # Error codes
    ERROR = 'AUDIT_ERROR'
    CREATION_FAILED = 'AUDIT_CREATION_FAILED'
    RETRIEVAL_FAILED = 'AUDIT_RETRIEVAL_FAILED'
    INVALID_REQUEST = 'AUDIT_INVALID_REQUEST'
    PERMISSION_DENIED = 'AUDIT_PERMISSION_DENIED'
    USER_NOT_FOUND = 'AUDIT_USER_NOT_FOUND'
    CONFIGURATION_ERROR = 'AUDIT_CONFIG_ERROR'
