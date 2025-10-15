# LDC Dashboard RBAC - Django Feature-Based Role Access Control with Onboarding

A comprehensive Django app for implementing feature-based role-based access control (RBAC) with group-level permissions and complete user onboarding system.

## Features

- **Feature-based permissions** - Control access to specific features/views
- **Role hierarchy** - Superadmin, Admin, and User roles with different access levels
- **Group management** - Organize users into groups with shared permissions
- **Permission levels** - Support for read, write, and admin access levels
- **User onboarding** - Complete registration, approval, and password management system
- **Email integration** - Configurable email service for notifications and password resets
- **Token-based security** - Secure password reset with expiration tokens
- **Flexible configuration** - Works with any authentication system
- **Performance optimized** - Built-in bulk operations and efficient queries
- **Management commands** - CLI tools for feature synchronization and status checking
- **Backend only** - No frontend dependencies, use your own UI
- **Lightweight** - Minimal dependencies, maximum flexibility
- **Django Rest Framework support** - Optional DRF permission classes
- **Role-based bypass** - Automatic access for superadmin and admin users

## Installation

```bash
pip install ldc-dashboard-rbac
```

## Quick Start

1. Add `ldc_dashboard_rbac` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... your apps
    'ldc_dashboard_rbac',
]
```

2. Configure the package in your settings:

```python
# User getter function - adapt to your authentication system
def get_current_user(request):
    return getattr(request, 'user', None)

def is_super_admin(user):
    return user and user.is_superadmin

def is_admin(user):
    return user and user.is_admin

GROUP_RBAC = {
    'USER_MODEL': 'dashboard.DashboardUser',  # Your user model
    'USER_GETTER': get_current_user,
    'SUPER_ADMIN_CHECK': is_super_admin,
    'ADMIN_CHECK': is_admin,
    'FEATURE_MODEL': 'dashboard.Feature',  # Your feature model
    'GROUP_MODEL': 'dashboard.Group',  # Your group model
    'USER_GROUP_MODEL': 'dashboard.UserGroupMembership',  # Your user-group model
    'GROUP_FEATURE_PERMISSION_MODEL': 'dashboard.GroupFeaturePermission',  # Your permission model
    'PASSWORD_RESET_MODEL': 'dashboard.PasswordResetToken',  # Your password reset model
}

# Email configuration (optional)
RBAC_EMAIL_CONFIG = {
    'FROM_EMAIL': 'noreply@yourdomain.com',
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
}

# Site URL for email links
SITE_URL = 'https://yourdomain.com'
```

3. Run migrations:

```bash
python manage.py migrate
```

4. Sync features from your URLs:

```bash
python manage.py sync_features
```

5. Check RBAC status:

```bash
python manage.py rbac_status
```

## Usage

### In Views (Decorators)

```python
from ldc_dashboard_rbac.decorators import feature_required, admin_required, superadmin_required

@feature_required('user_management')
def user_list(request):
    # Only users with 'user_management' feature access can view this
    # Superadmin and Admin users have automatic access
    return render(request, 'users/list.html')

@feature_required('user_management', permission_level='admin')
def user_delete(request, user_id):
    # Only users with admin-level access to user_management
    # Superadmin and Admin users have automatic access
    return redirect('user_list')

@admin_required
def admin_panel(request):
    # Only admin and superadmin users can access this
    return render(request, 'admin/panel.html')

@superadmin_required
def superadmin_panel(request):
    # Only superadmin users can access this
    return render(request, 'superadmin/panel.html')
```

### In Class-Based Views

```python
from ldc_dashboard_rbac.decorators import feature_required

class UserManagementView(ListView):
    model = User
    
    @feature_required('user_management')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
```

### Programmatic Permission Checking

```python
from ldc_dashboard_rbac.permissions import user_has_feature_permission, get_user_features, is_superadmin_user, is_admin_user

# Check single permission
if user_has_feature_permission(request.user, 'user_management', 'write'):
    # User can edit users
    pass

# Get all user's features
user_features = get_user_features(request.user)
for feature in user_features:
    print(f"User has access to: {feature.name}")

# Check user roles
if is_superadmin_user(request.user):
    # User has superadmin privileges
    pass

if is_admin_user(request.user):
    # User has admin privileges
    pass
```

### Django Rest Framework Support

```python
from rest_framework.views import APIView
from ldc_dashboard_rbac.drf_permissions import HasFeaturePermission, IsFeatureAdmin, IsSuperAdmin

class UserAPIView(APIView):
    permission_classes = [HasFeaturePermission]
    required_feature = 'user_management'
    required_permission_level = 'read'
    
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsFeatureAdmin()]
        return [HasFeaturePermission()]

class SuperAdminAPIView(APIView):
    permission_classes = [IsSuperAdmin]
    
    def get(self, request, format=None):
        # Only superadmin users can access this
        return Response({'message': 'Superadmin access granted'})
```

### User Onboarding

The package includes complete onboarding views:

```python
# In your urls.py
from ldc_dashboard_rbac.onboarding import (
    RegistrationView,
    AdminRegistrationView,
    ResetPasswordView,
    SetPasswordView,
    UserApprovalView,
)

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('admin/register/', AdminRegistrationView.as_view(), name='admin_register'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('set-password/<uuid:token>/', SetPasswordView.as_view(), name='set_password'),
    path('admin/approvals/', UserApprovalView.as_view(), name='user_approvals'),
]
```

### In Your Own Templates

Since this is backend-only, you implement your own template logic:

```python
# In your view
def my_view(request):
    from ldc_dashboard_rbac.permissions import user_has_feature_permission, is_admin_user, is_superadmin_user
    
    context = {
        'can_manage_users': user_has_feature_permission(request.user, 'user_management'),
        'can_view_reports': user_has_feature_permission(request.user, 'reports', 'read'),
        'is_admin': is_admin_user(request.user),
        'is_superadmin': is_superadmin_user(request.user),
    }
    return render(request, 'my_template.html', context)
```

```html
<!-- In your template -->
{% if can_manage_users %}
    <a href="{% url 'user_list' %}">Manage Users</a>
{% endif %}

{% if is_admin %}
    <button class="delete-user">Delete User</button>
{% endif %}

{% if is_superadmin %}
    <a href="{% url 'superadmin_panel' %}">Superadmin Panel</a>
{% endif %}
```

## Configuration

The package uses the `GROUP_RBAC` setting in your Django settings. Here are all available options:

```python
GROUP_RBAC = {
    # Required settings
    'USER_MODEL': 'dashboard.DashboardUser',  # Your user model path
    'USER_GETTER': get_current_user,  # Function to get user from request
    
    # Optional settings
    'SUPER_ADMIN_CHECK': is_super_admin,  # Function to check superadmin status
    'ADMIN_CHECK': is_admin,  # Function to check admin status
    
    # Model paths (defaults to dashboard app)
    'FEATURE_MODEL': 'dashboard.Feature',
    'GROUP_MODEL': 'dashboard.Group',
    'USER_GROUP_MODEL': 'dashboard.UserGroupMembership',
    'GROUP_FEATURE_PERMISSION_MODEL': 'dashboard.GroupFeaturePermission',
    'PASSWORD_RESET_MODEL': 'dashboard.PasswordResetToken',
}

# Email configuration (optional)
RBAC_EMAIL_CONFIG = {
    'FROM_EMAIL': 'noreply@yourdomain.com',
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
}

# Site URL for email links
SITE_URL = 'https://yourdomain.com'
```

## Management Commands

### sync_features

Sync features from your URL patterns or predefined list:

```bash
python manage.py sync_features
python manage.py sync_features --dry-run  # Preview changes
python manage.py sync_features --from-urls  # Auto-discover from URLs
```

### rbac_status

Check the current RBAC configuration and status:

```bash
python manage.py rbac_status
python manage.py rbac_status --validate  # Validate configuration
python manage.py rbac_status --user username  # Show user permissions
```

## API Response Handling

The package automatically handles both web and API requests:

- **Web requests**: Returns HTML permission denied page
- **API requests**: Returns JSON error response

API responses include:

```json
{
    "error": "You don't have permission to access this feature.",
    "feature": "user_management",
    "required_permission": "write"
}
```

## Abstract Models

The package provides abstract models that you can inherit from:

```python
from ldc_dashboard_rbac.models import (
    AbstractFeature,
    AbstractDashboardUser,
    AbstractGroup,
    AbstractUserGroupMembership,
    AbstractGroupFeaturePermission,
    AbstractPasswordResetToken,
)

class Feature(AbstractFeature):
    pass

class DashboardUser(AbstractDashboardUser):
    pass

class Group(AbstractGroup):
    users = models.ManyToManyField(
        DashboardUser,
        through='UserGroupMembership',
        related_name='user_groups',
        blank=True
    )
    features = models.ManyToManyField(
        Feature,
        through='GroupFeaturePermission',
        related_name='feature_groups',
        blank=True
    )

class UserGroupMembership(AbstractUserGroupMembership):
    user = models.ForeignKey(DashboardUser, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

class GroupFeaturePermission(AbstractGroupFeaturePermission):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)

class PasswordResetToken(AbstractPasswordResetToken):
    user = models.ForeignKey(DashboardUser, on_delete=models.CASCADE)
```

## Permission Levels

The package supports three permission levels:

- **read**: View-only access
- **write**: Read and write access (includes read)
- **admin**: Full administrative access (includes read and write)

## Role Hierarchy

The package implements a three-tier role hierarchy:

- **Superadmin**: All access + can grant/revoke admin role to users
- **Admin**: All access to features and groups
- **User**: Feature-level access via groups

## Role-Based Bypass

Users identified as superadmin or admin automatically bypass all permission checks. This is configured via the `SUPER_ADMIN_CHECK` and `ADMIN_CHECK` functions in your settings.

## Error Handling

The package includes comprehensive error handling and logging. Check your Django logs for detailed information about permission checks and configuration issues.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:

- GitHub Issues: https://github.com/nishantbaruahldc/ldc-dashboard-rbac/issues
- Documentation: https://ldc-dashboard-rbac.readthedocs.io/