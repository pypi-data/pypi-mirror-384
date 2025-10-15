"""
Django Rest Framework permission classes for feature-based access control with role hierarchy
"""
from rest_framework.permissions import BasePermission
from ldc_dashboard_rbac.permissions import user_has_feature_permission, is_superadmin_user, is_admin_user, get_rbac_config
import logging

logger = logging.getLogger(__name__)


class HasFeaturePermission(BasePermission):
    """
    DRF permission class to check if a user has permission for a specific feature.

    Role hierarchy:
    - Superadmin: All access
    - Admin: All access  
    - User: Feature-level access via groups

    Usage:
        class MyAPIView(APIView):
            permission_classes = [IsAuthenticated, HasFeaturePermission]
            required_feature = 'my_feature_url_name'
            required_permission_level = 'read'  # optional, defaults to 'read'
            
            def get(self, request, format=None):
                # Your API logic here
                return Response({'message': 'Success'})
    """
    
    def has_permission(self, request, view):
        # Get the required feature from the view
        feature_url_name = getattr(view, 'required_feature', None)
        if not feature_url_name:
            logger.warning(f"View {view.__class__.__name__} has HasFeaturePermission but no 'required_feature' attribute")
            return False
        
        # Get permission level (defaults to 'read')
        permission_level = getattr(view, 'required_permission_level', 'read')
        
        # Get user using the configured user getter
        config = get_rbac_config()
        user_getter = config.get('USER_GETTER')
        
        if not user_getter:
            logger.error("USER_GETTER not configured in GROUP_RBAC settings")
            return False
        
        user = user_getter(request)
        
        # ✅ SUPERADMIN BYPASS: Always allow superadmin access
        if is_superadmin_user(user):
            logger.info(f"Superadmin {user} granted access to {feature_url_name} via DRF permission")
            return True
        
        # ✅ ADMIN BYPASS: Always allow admin access
        if is_admin_user(user):
            logger.info(f"Admin {user} granted access to {feature_url_name} via DRF permission")
            return True
        
        # Regular permission check for users
        return user_has_feature_permission(user, feature_url_name, permission_level)


class IsFeatureAdmin(BasePermission):
    """
    DRF permission class to check if a user is admin or superadmin.
    
    Usage:
        class MyAdminAPIView(APIView):
            permission_classes = [IsAuthenticated, IsFeatureAdmin]
            
            def get(self, request, format=None):
                # Admin-only API logic here
                return Response({'message': 'Admin access granted'})
    """
    
    def has_permission(self, request, view):
        # Get user using the configured user getter
        config = get_rbac_config()
        user_getter = config.get('USER_GETTER')
        
        if not user_getter:
            logger.error("USER_GETTER not configured in GROUP_RBAC settings")
            return False
        
        user = user_getter(request)
        return is_admin_user(user) or is_superadmin_user(user)


class IsSuperAdmin(BasePermission):
    """
    DRF permission class to check if a user is superadmin only.
    
    Usage:
        class MySuperAdminAPIView(APIView):
            permission_classes = [IsAuthenticated, IsSuperAdmin]
            
            def get(self, request, format=None):
                # Superadmin-only API logic here
                return Response({'message': 'Superadmin access granted'})
    """
    
    def has_permission(self, request, view):
        # Get user using the configured user getter
        config = get_rbac_config()
        user_getter = config.get('USER_GETTER')
        
        if not user_getter:
            logger.error("USER_GETTER not configured in GROUP_RBAC settings")
            return False
        
        user = user_getter(request)
        return is_superadmin_user(user)


class DynamicFeaturePermission(BasePermission):
    """
    DRF permission class that allows dynamic feature checking based on URL parameters.
    
    Usage:
        class MyAPIView(APIView):
            permission_classes = [IsAuthenticated, DynamicFeaturePermission]
            
            def get_required_feature(self):
                # You can implement custom logic here
                # For example, based on URL parameters or request data
                return f"feature_{self.kwargs.get('feature_type', 'default')}"
            
            def get(self, request, format=None):
                return Response({'message': 'Success'})
    """
    
    def has_permission(self, request, view):
        # Check if view has a method to determine the required feature
        if hasattr(view, 'get_required_feature'):
            feature_url_name = view.get_required_feature()
        else:
            # Fallback to the static attribute
            feature_url_name = getattr(view, 'required_feature', None)
        
        if not feature_url_name:
            logger.warning(f"View {view.__class__.__name__} has DynamicFeaturePermission but no way to determine required feature")
            return False
        
        # Get permission level (defaults to 'read')
        permission_level = getattr(view, 'required_permission_level', 'read')
        if hasattr(view, 'get_required_permission_level'):
            permission_level = view.get_required_permission_level()
        
        # Get user using the configured user getter
        config = get_rbac_config()
        user_getter = config.get('USER_GETTER')
        
        if not user_getter:
            logger.error("USER_GETTER not configured in GROUP_RBAC settings")
            return False
        
        user = user_getter(request)
        
        # ✅ SUPERADMIN BYPASS: Always allow superadmin access
        if is_superadmin_user(user):
            logger.info(f"Superadmin {user} granted access to {feature_url_name} via DynamicFeaturePermission")
            return True
        
        # ✅ ADMIN BYPASS: Always allow admin access
        if is_admin_user(user):
            logger.info(f"Admin {user} granted access to {feature_url_name} via DynamicFeaturePermission")
            return True
        
        # Regular permission check for users
        return user_has_feature_permission(user, feature_url_name, permission_level)