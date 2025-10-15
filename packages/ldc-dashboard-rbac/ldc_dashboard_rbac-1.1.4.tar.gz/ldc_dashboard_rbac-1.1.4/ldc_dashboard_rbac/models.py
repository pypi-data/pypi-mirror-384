"""
Abstract models for feature-based RBAC system - Simplified Version
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import uuid

from ldc_dashboard_rbac.base_models import DefaultTimeStamp
from ldc_dashboard_rbac.constants import (
    UserRoles, FieldLengths, Defaults
)


class AbstractFeature(DefaultTimeStamp):
    """Abstract base model for features"""
    name = models.CharField(max_length=FieldLengths.FEATURE_NAME_MAX_LENGTH, unique=True)
    url_name = models.CharField(max_length=FieldLengths.FEATURE_URL_NAME_MAX_LENGTH, unique=True)
    description = models.TextField(null=True)
    is_active = models.BooleanField(default=Defaults.FEATURE_ACTIVE)
    category = models.CharField(max_length=FieldLengths.FEATURE_CATEGORY_MAX_LENGTH, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        abstract = True


class AbstractDashboardUser(DefaultTimeStamp):
    """Abstract base model for dashboard users"""
    name = models.CharField(max_length=FieldLengths.USER_NAME_MAX_LENGTH)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=FieldLengths.USER_PASSWORD_MAX_LENGTH)
    is_active = models.BooleanField(default=Defaults.USER_ACTIVE)  # Requires admin approval
    role = models.CharField(
        max_length=FieldLengths.USER_ROLE_MAX_LENGTH, 
        choices=UserRoles.CHOICES, 
        default=Defaults.DEFAULT_USER_ROLE
    )
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def set_password(self, raw_password):
        """Set password using Django's password hashing"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check password using Django's password checking"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)
    
    @property
    def is_superadmin(self):
        return self.role == UserRoles.SUPERADMIN
    
    @property
    def is_admin(self):
        return self.role in UserRoles.ADMIN_ROLES
    
    class Meta:
        abstract = True


class AbstractGroup(DefaultTimeStamp):
    """
    Abstract base model for groups with feature-level permissions
    
    NOTE: ManyToMany relationships must be defined in concrete models because:
    1. Abstract models can't reference concrete models directly
    2. Through models must be concrete, not abstract
    3. Related names would conflict across different implementations
    
    In your concrete model, define the relationships like this:
    
    class Group(AbstractGroup):
        users = models.ManyToManyField(
            User,  # Your concrete User model
            through='UserGroupMembership',  # Your concrete through model
            related_name='user_groups'
        )
        features = models.ManyToManyField(
            Feature,  # Your concrete Feature model
            through='GroupFeaturePermission',  # Your concrete through model
            related_name='feature_groups'
        )
    """
    group_name = models.CharField(max_length=FieldLengths.GROUP_NAME_MAX_LENGTH, unique=True)
    description = models.TextField(null=True)
    is_active = models.BooleanField(default=Defaults.GROUP_ACTIVE)
    
    def __str__(self):
        return self.group_name
    
    class Meta:
        abstract = True


class AbstractUserGroupMembership(DefaultTimeStamp):
    """
    Abstract base model for user-group memberships
    
    NOTE: ForeignKey relationships must be defined in concrete models because
    abstract models can't reference other concrete models properly.
    
    In your concrete model, define the relationships like this:
    
    class UserGroupMembership(AbstractUserGroupMembership):
        user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
        group = models.ForeignKey(Group, on_delete=models.DO_NOTHING)
        
        class Meta:
            unique_together = ('user', 'group')
    """
    is_active = models.BooleanField(default=Defaults.MEMBERSHIP_ACTIVE)
    
    class Meta:
        abstract = True


class AbstractGroupFeaturePermission(DefaultTimeStamp):
    """
    Abstract base model for group-feature permissions - Simplified Version
    Only tracks if a group has access to a feature (no permission levels)
    
    NOTE: ForeignKey relationships must be defined in concrete models because
    abstract models can't reference other concrete models properly.
    
    In your concrete model, define the relationships like this:
    
    class GroupFeaturePermission(AbstractGroupFeaturePermission):
        group = models.ForeignKey(Group, on_delete=models.DO_NOTHING)
        feature = models.ForeignKey(Feature, on_delete=models.DO_NOTHING)
        
        class Meta:
            unique_together = ('group', 'feature')
    """
    is_enabled = models.BooleanField(default=Defaults.PERMISSION_ENABLED)
    
    class Meta:
        abstract = True


class AbstractPasswordResetToken(models.Model):
    """
    Abstract base model for password reset tokens
    
    NOTE: ForeignKey relationship must be defined in concrete models because
    abstract models can't reference other concrete models properly.
    
    In your concrete model, define the relationship like this:
    
    class PasswordResetToken(AbstractPasswordResetToken):
        user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    """
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=Defaults.TOKEN_USED)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        """Check if token is valid and not expired"""
        return not self.is_used and timezone.now() < self.expires_at
    
    class Meta:
        abstract = True


# Backward compatibility aliases
AbstractUserGroup = AbstractUserGroupMembership