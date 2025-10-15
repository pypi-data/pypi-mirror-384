"""
Audit Trail Package for LDC Dashboard RBAC

This package provides a generic, reusable audit trail system that can be integrated
into any Django project. It tracks user actions, changes, and system events.

Main Components:
- AbstractAuditTrail: Base model for audit trails
- AuditTrailManager: Manager for audit trail operations
- Decorators: Easy integration decorators
- Middleware: Automatic tracking middleware
- Helpers: Utility functions for common operations
"""

from .models import AbstractAuditTrail, AbstractAuditTrailManager
from .operations import (
    create_audit_trail_entry,
    get_audit_trail_logs,
    bulk_create_audit_entries,
    get_audit_stats,
    cleanup_old_audit_entries,
    AuditTrailOperationError,
)
from .helpers import (
    create_audit_log_helper,
    get_audit_trail_list_helper,
    get_audit_trail_context_helper,
    get_user_audit_summary_helper,
)
from .decorators import (
    audit_trail,
    audit_trail_async,
)
from .constants import (
    AuditTrailActionTypes,
    AuditTrailEntityTypes,
    AuditTrailConstants,
    AuditTrailFieldLengths,
    AuditTrailSettings,
    MessageCodes,
)
from .utils import (
    get_client_ip,
    get_user_agent,
    get_trace_id,
    sanitize_audit_data,
    extract_changes,
    format_audit_details,
    validate_audit_config,
    serialize_for_audit,
    create_audit_context,
)
from .validators import (
    GetAuditTrailRequest,
    CreateAuditTrailRequest,
    AuditTrailStatsRequest,
    UserAuditSummaryRequest,
    BulkCreateAuditTrailRequest,
    AuditTrailCleanupRequest,
    AuditTrailExportRequest,
)
from .middleware import AuditTrailMiddleware
from .signals import audit_rbac_event

__all__ = [
    # Models
    'AbstractAuditTrail',
    'AbstractAuditTrailManager',
    
    # Operations
    'create_audit_trail_entry',
    'get_audit_trail_logs',
    'bulk_create_audit_entries',
    'get_audit_stats',
    'cleanup_old_audit_entries',
    'AuditTrailOperationError',
    
    # Helpers
    'create_audit_log_helper',
    'get_audit_trail_list_helper',
    'get_audit_trail_context_helper',
    'get_user_audit_summary_helper',
    
    # Decorators
    'audit_trail',
    'audit_trail_async',
    
    # Constants
    'AuditTrailActionTypes',
    'AuditTrailEntityTypes',
    'AuditTrailConstants',
    'AuditTrailFieldLengths',
    'AuditTrailSettings',
    'MessageCodes',
    
    # Utils
    'get_client_ip',
    'get_user_agent',
    'get_trace_id',
    'sanitize_audit_data',
    'extract_changes',
    'format_audit_details',
    'validate_audit_config',
    'serialize_for_audit',
    'create_audit_context',
    
    # Validators
    'GetAuditTrailRequest',
    'CreateAuditTrailRequest',
    'AuditTrailStatsRequest',
    'UserAuditSummaryRequest',
    'BulkCreateAuditTrailRequest',
    'AuditTrailCleanupRequest',
    'AuditTrailExportRequest',
    
    # Middleware
    'AuditTrailMiddleware',
    
    # Signals
    'audit_rbac_event',
]

# Version information
__version__ = '1.0.0'
__author__ = 'LDC Dashboard RBAC Team'

# Configuration validation on import
# try:
#     from .utils import validate_audit_config
#     validation_result = validate_audit_config()
#     if not validation_result['is_valid']:
#         import logging
#         logger = logging.getLogger(__name__)
#         logger.warning("Audit Trail configuration issues found:")
#         for error in validation_result['errors']:
#             logger.error(f"  - {error}")
#         for warning in validation_result['warnings']:
#             logger.warning(f"  - {warning}")
# except Exception:
#     pass  # Don't break import if validation fails
