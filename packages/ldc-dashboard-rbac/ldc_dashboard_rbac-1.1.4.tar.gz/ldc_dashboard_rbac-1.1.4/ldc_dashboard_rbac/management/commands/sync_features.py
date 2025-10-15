from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from ldc_dashboard_rbac.permissions import get_rbac_config
from ldc_dashboard_rbac.constants import SettingsKeys, DefaultModelPaths


class Command(BaseCommand):
    help = 'Sync features from URL patterns'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
        parser.add_argument(
            '--include-inactive',
            action='store_true',
            help='Include inactive URL patterns (default: only active)',
        )
        parser.add_argument(
            '--category',
            type=str,
            default='Auto-discovered',
            help='Default category for discovered features',
        )
    
    def handle(self, *args, **options):
        config = get_rbac_config()
        feature_model = apps.get_model(
            config.get(SettingsKeys.GroupRBAC.FEATURE_MODEL, DefaultModelPaths.FEATURE)
        )
        
        # Only do URL discovery - remove hardcoded features
        self.sync_from_urls(feature_model, options)
    
    def sync_from_urls(self, feature_model, options):
        """Sync features from Django URL patterns"""
        from django.urls import get_resolver
        
        try:
            resolver = get_resolver()
            created_count = 0
            
            def extract_url_names(url_patterns, namespace=''):
                """Recursively extract URL names from patterns"""
                names = []
                for pattern in url_patterns:
                    if hasattr(pattern, 'name') and pattern.name:
                        full_name = f"{namespace}:{pattern.name}" if namespace else pattern.name
                        names.append(full_name)
                    elif hasattr(pattern, 'url_patterns'):
                        # Handle included URL patterns
                        pattern_namespace = getattr(pattern, 'namespace', '')
                        if pattern_namespace:
                            pattern_namespace = f"{namespace}:{pattern_namespace}" if namespace else pattern_namespace
                        names.extend(extract_url_names(pattern.url_patterns, pattern_namespace))
                return names
            
            url_names = extract_url_names(resolver.url_patterns)
            
            for url_name in url_names:
                if not feature_model.objects.filter(url_name=url_name).exists():
                    # Create a human-readable name from URL name
                    display_name = url_name.replace('_', ' ').replace(':', ' - ').title()
                    
                    if options['dry_run']:
                        self.stdout.write(f"Would create: {display_name} ({url_name})")
                        continue
                    
                    feature_model.objects.create(
                        name=display_name,
                        url_name=url_name,
                        description=f"Auto-generated feature for {url_name}",
                        category=options['category'],
                        is_active=not options['include_inactive']  # Start as inactive for security
                    )
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Created feature: {display_name}")
                    )
            
            if not options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully synced {created_count} features from URLs")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error syncing features from URLs: {e}")
            )