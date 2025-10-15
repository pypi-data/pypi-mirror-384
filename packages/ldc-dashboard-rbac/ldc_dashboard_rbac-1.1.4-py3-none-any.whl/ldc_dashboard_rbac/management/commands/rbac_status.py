"""
Management command to show RBAC status and configuration
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count
from ldc_dashboard_rbac.utils import validate_rbac_configuration, get_user_permission_summary
from ldc_dashboard_rbac.permissions import get_models
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Show RBAC status and configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Show permissions for a specific user (username)',
        )
        
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate RBAC configuration',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== GROUP RBAC STATUS ===\n'))
        
        # Validate configuration if requested
        if options['validate']:
            self.stdout.write(self.style.HTTP_INFO('Configuration Validation:'))
            issues = validate_rbac_configuration()
            if issues:
                for issue in issues:
                    self.stdout.write(self.style.ERROR(f'  ❌ {issue}'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✅ Configuration is valid'))
            self.stdout.write('')
        
        try:
            User, Feature, Group, UserGroupMembership, GroupFeaturePermission, PasswordResetToken = get_models()
            
            # Show statistics
            self.stdout.write(self.style.HTTP_INFO('Statistics:'))
            self.stdout.write(f'  Users: {User.objects.count()} total, {User.objects.filter(is_active=True).count()} active')
            self.stdout.write(f'  Features: {Feature.objects.count()} total, {Feature.objects.filter(is_active=True).count()} active')
            self.stdout.write(f'  Groups: {Group.objects.count()} total, {Group.objects.filter(is_active=True).count()} active')
            self.stdout.write(f'  Permissions: {GroupFeaturePermission.objects.count()} total, {GroupFeaturePermission.objects.filter(is_enabled=True).count()} enabled')
            self.stdout.write(f'  User-Group Memberships: {UserGroupMembership.objects.count()} total, {UserGroupMembership.objects.filter(is_active=True).count()} active')
            self.stdout.write(f'  Password Reset Tokens: {PasswordResetToken.objects.count()} total, {PasswordResetToken.objects.filter(is_used=False).count()} active')
            self.stdout.write('')
            
            # Show user roles
            self.stdout.write(self.style.HTTP_INFO('User Roles:'))
            role_counts = User.objects.values('role').annotate(count=Count('role'))
            for role_data in role_counts:
                role = role_data['role']
                count = role_data['count']
                self.stdout.write(f'  {role}: {count} users')
            self.stdout.write('')
            
            # Show feature categories
            categories = Feature.objects.values_list('category', flat=True).distinct().exclude(category__isnull=True).exclude(category='')
            if categories:
                self.stdout.write(self.style.HTTP_INFO('Feature Categories:'))
                for category in sorted(categories):
                    count = Feature.objects.filter(category=category).count()
                    self.stdout.write(f'  {category}: {count} features')
                self.stdout.write('')
            
            # Show user permissions if requested
            if options['user']:
                UserModel = get_user_model()
                try:
                    user = UserModel.objects.get(username=options['user'])
                    self.show_user_permissions(user)
                except UserModel.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User "{options["user"]}" not found'))
            
            # Show configuration
            config = getattr(settings, 'GROUP_RBAC', {})
            self.stdout.write(self.style.HTTP_INFO('Configuration:'))
            self.stdout.write(f'  USER_MODEL: {config.get("USER_MODEL", "dashboard.DashboardUser")}')
            self.stdout.write(f'  FEATURE_MODEL: {config.get("FEATURE_MODEL", "dashboard.Feature")}')
            self.stdout.write(f'  GROUP_MODEL: {config.get("GROUP_MODEL", "dashboard.Group")}')
            self.stdout.write(f'  USER_GROUP_MODEL: {config.get("USER_GROUP_MODEL", "dashboard.UserGroupMembership")}')
            self.stdout.write(f'  GROUP_FEATURE_PERMISSION_MODEL: {config.get("GROUP_FEATURE_PERMISSION_MODEL", "dashboard.GroupFeaturePermission")}')
            self.stdout.write(f'  PASSWORD_RESET_MODEL: {config.get("PASSWORD_RESET_MODEL", "dashboard.PasswordResetToken")}')
            self.stdout.write(f'  USER_GETTER: {"✅ Set" if config.get("USER_GETTER") else "❌ Not set"}')
            self.stdout.write(f'  SUPER_ADMIN_CHECK: {"✅ Set" if config.get("SUPER_ADMIN_CHECK") else "❌ Not set"}')
            self.stdout.write(f'  ADMIN_CHECK: {"✅ Set" if config.get("ADMIN_CHECK") else "❌ Not set"}')
            
            # Show email configuration
            email_config = getattr(settings, 'RBAC_EMAIL_CONFIG', {})
            self.stdout.write(self.style.HTTP_INFO('Email Configuration:'))
            self.stdout.write(f'  FROM_EMAIL: {email_config.get("FROM_EMAIL", "Not set")}')
            self.stdout.write(f'  EMAIL_BACKEND: {email_config.get("EMAIL_BACKEND", "Django default")}')
            self.stdout.write(f'  SITE_URL: {getattr(settings, "SITE_URL", "Not set")}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting RBAC status: {e}'))
    
    def show_user_permissions(self, user):
        """Show detailed permissions for a specific user"""
        # Try to get username or email
        username = getattr(user, 'username', None) or getattr(user, 'email', None) or str(user)
        self.stdout.write(self.style.HTTP_INFO(f'User Permissions for "{username}":'))
        
        summary = get_user_permission_summary(user)
        
        self.stdout.write(f'  Role: {summary["role"]}')
        self.stdout.write(f'  Is Superadmin: {summary["is_superadmin"]}')
        self.stdout.write(f'  Is Admin: {summary["is_admin"]}')
        self.stdout.write(f'  Groups ({summary["total_groups"]}):')
        for group in summary['groups']:
            group_name = group.get('group_name', group.get('name', 'Unknown'))
            self.stdout.write(f'    - {group_name}')
        
        self.stdout.write(f'  Features ({summary["total_features"]}):')
        for feature in summary['features']:
            permission_level = summary['permission_levels'].get(feature['url_name'], 'read')
            category = f" [{feature['category']}]" if feature['category'] else ""
            self.stdout.write(f'    - {feature["name"]} ({permission_level}){category}')
        
        self.stdout.write('')