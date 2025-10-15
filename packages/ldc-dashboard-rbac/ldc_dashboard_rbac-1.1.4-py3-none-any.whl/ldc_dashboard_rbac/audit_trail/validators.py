"""
Pydantic validators for audit trail functionality
"""
from pydantic.v1 import BaseModel, Field, validator
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from .constants import AuditTrailActionTypes, AuditTrailEntityTypes, AuditTrailConstants


class GetAuditTrailRequest(BaseModel):
    """Validator for audit trail list request"""
    
    user_username: Optional[str] = Field(
        None, 
        description="Filter by username (partial match)",
        max_length=150
    )
    action_type: Optional[str] = Field(
        None, 
        description="Filter by a specific action type"
    )
    entity_type: Optional[str] = Field(
        None, 
        description="Filter by a specific entity type"
    )
    entity_id: Optional[int] = Field(
        None, 
        description="Filter by specific entity ID",
        ge=1
    )
    start_date: Optional[str] = Field(
        None, 
        description="Start date for filtering (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, 
        description="End date for filtering (YYYY-MM-DD)"
    )
    is_successful: Optional[bool] = Field(
        None, 
        description="Filter by success status"
    )
    trace_id: Optional[str] = Field(
        None, 
        description="Filter by trace ID",
        max_length=100
    )
    page: int = Field(
        1, 
        ge=1, 
        description="Page number for pagination"
    )
    limit: int = Field(
        AuditTrailConstants.DEFAULT_PAGE_SIZE, 
        ge=1, 
        le=AuditTrailConstants.MAX_PAGE_SIZE, 
        description="Number of records per page"
    )

    @validator('start_date', 'end_date', pre=True, allow_reuse=True)
    def validate_date_format(cls, v):
        """Validate date format"""
        if v is None:
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

    @validator('action_type', allow_reuse=True)
    def validate_action_type(cls, v):
        """Validate action type"""
        if v is None:
            return v
        
        valid_actions = [choice[0] for choice in AuditTrailActionTypes.CHOICES]
        if v not in valid_actions:
            raise ValueError(f"Invalid action type. Must be one of: {', '.join(valid_actions)}")
        return v

    @validator('entity_type', allow_reuse=True)
    def validate_entity_type(cls, v):
        """Validate entity type"""
        if v is None:
            return v
        
        # Allow any entity type since projects can extend the list
        if len(v.strip()) == 0:
            raise ValueError("Entity type cannot be empty")
        return v.strip()

    @validator('end_date', allow_reuse=True)
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date"""
        if v is None or 'start_date' not in values or values['start_date'] is None:
            return v
        
        start_date = datetime.strptime(values['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(v, '%Y-%m-%d').date()
        
        if end_date < start_date:
            raise ValueError("End date must be after or equal to start date")
        
        return v


class CreateAuditTrailRequest(BaseModel):
    """Validator for creating audit trail entries"""
    
    action_type: str = Field(
        ..., 
        description="Type of action performed"
    )
    entity_type: str = Field(
        ..., 
        description="Type of entity affected"
    )
    entity_id: int = Field(
        ..., 
        description="ID of the entity",
        ge=1
    )
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional details about the action"
    )
    old_values: Optional[Dict[str, Any]] = Field(
        None, 
        description="Previous values before the change"
    )
    new_values: Optional[Dict[str, Any]] = Field(
        None, 
        description="New values after the change"
    )
    is_successful: bool = Field(
        True, 
        description="Whether the action was successful"
    )
    error_message: Optional[str] = Field(
        None, 
        description="Error message if action failed",
        max_length=1000
    )

    @validator('action_type', allow_reuse=True)
    def validate_action_type(cls, v):
        """Validate action type"""
        valid_actions = [choice[0] for choice in AuditTrailActionTypes.CHOICES]
        if v not in valid_actions:
            raise ValueError(f"Invalid action type. Must be one of: {', '.join(valid_actions)}")
        return v

    @validator('entity_type', allow_reuse=True)
    def validate_entity_type(cls, v):
        """Validate entity type"""
        if len(v.strip()) == 0:
            raise ValueError("Entity type cannot be empty")
        return v.strip()

    @validator('details', 'old_values', 'new_values', allow_reuse=True)
    def validate_json_fields(cls, v):
        """Validate JSON fields"""
        if v is None:
            return {}
        
        if not isinstance(v, dict):
            raise ValueError("Field must be a dictionary")
        
        return v


class AuditTrailStatsRequest(BaseModel):
    """Validator for audit trail statistics request"""
    
    start_date: Optional[str] = Field(
        None, 
        description="Start date for statistics (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, 
        description="End date for statistics (YYYY-MM-DD)"
    )
    user_username: Optional[str] = Field(
        None, 
        description="Filter by specific user",
        max_length=150
    )
    action_types: Optional[List[str]] = Field(
        None, 
        description="List of action types to include"
    )
    entity_types: Optional[List[str]] = Field(
        None, 
        description="List of entity types to include"
    )

    @validator('start_date', 'end_date', pre=True, allow_reuse=True)
    def validate_date_format(cls, v):
        """Validate date format"""
        if v is None:
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

    @validator('action_types', allow_reuse=True)
    def validate_action_types(cls, v):
        """Validate action types list"""
        if v is None:
            return v
        
        valid_actions = [choice[0] for choice in AuditTrailActionTypes.CHOICES]
        invalid_actions = [action for action in v if action not in valid_actions]
        
        if invalid_actions:
            raise ValueError(f"Invalid action types: {', '.join(invalid_actions)}")
        
        return v

    @validator('entity_types', allow_reuse=True)
    def validate_entity_types(cls, v):
        """Validate entity types list"""
        if v is None:
            return v
        
        # Allow any entity types since projects can extend the list
        invalid_entities = [entity for entity in v if not entity.strip()]
        
        if invalid_entities:
            raise ValueError("Entity types cannot be empty")
        
        return [entity.strip() for entity in v]


class UserAuditSummaryRequest(BaseModel):
    """Validator for user audit summary request"""
    
    username: str = Field(
        ..., 
        description="Username to get summary for",
        max_length=150
    )
    days: int = Field(
        30, 
        description="Number of days to look back",
        ge=1,
        le=365
    )

    @validator('username', allow_reuse=True)
    def validate_username(cls, v):
        """Validate username"""
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v.strip()


class BulkCreateAuditTrailRequest(BaseModel):
    """Validator for bulk creating audit trail entries"""
    
    entries: List[CreateAuditTrailRequest] = Field(
        ..., 
        description="List of audit trail entries to create",
        min_items=1,
        max_items=1000  # Reasonable limit for bulk operations
    )

    @validator('entries', allow_reuse=True)
    def validate_entries_limit(cls, v):
        """Validate entries count"""
        if len(v) > 1000:
            raise ValueError("Cannot create more than 1000 entries at once")
        return v


class AuditTrailCleanupRequest(BaseModel):
    """Validator for audit trail cleanup request"""
    
    retention_days: int = Field(
        AuditTrailConstants.DEFAULT_RETENTION_DAYS,
        description="Number of days to retain audit entries",
        ge=1,
        le=3650  # 10 years maximum
    )
    dry_run: bool = Field(
        True,
        description="Whether to perform a dry run (count only, no deletion)"
    )

    @validator('retention_days', allow_reuse=True)
    def validate_retention_days(cls, v):
        """Validate retention days"""
        if v < 1:
            raise ValueError("Retention days must be at least 1")
        if v > 3650:
            raise ValueError("Retention days cannot exceed 3650 (10 years)")
        return v


class AuditTrailExportRequest(BaseModel):
    """Validator for audit trail export request"""
    
    format: str = Field(
        'csv',
        description="Export format (csv, json, xlsx)"
    )
    start_date: Optional[str] = Field(
        None, 
        description="Start date for export (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, 
        description="End date for export (YYYY-MM-DD)"
    )
    user_username: Optional[str] = Field(
        None, 
        description="Filter by username",
        max_length=150
    )
    action_types: Optional[List[str]] = Field(
        None, 
        description="List of action types to include"
    )
    entity_types: Optional[List[str]] = Field(
        None, 
        description="List of entity types to include"
    )
    include_details: bool = Field(
        True,
        description="Whether to include details in export"
    )
    max_records: int = Field(
        10000,
        description="Maximum number of records to export",
        ge=1,
        le=100000
    )

    @validator('format', allow_reuse=True)
    def validate_format(cls, v):
        """Validate export format"""
        valid_formats = ['csv', 'json', 'xlsx']
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid format. Must be one of: {', '.join(valid_formats)}")
        return v.lower()

    @validator('start_date', 'end_date', pre=True, allow_reuse=True)
    def validate_date_format(cls, v):
        """Validate date format"""
        if v is None:
            return v
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")
