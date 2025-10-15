"""
Onboarding views for user registration, admin registration, and password reset
"""
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.apps import apps
from django.db import transaction
from django.core.exceptions import ValidationError
from ldc_dashboard_rbac.permissions import get_rbac_config, is_superadmin_user, is_admin_user
from ldc_dashboard_rbac.utils import send_email
from ldc_dashboard_rbac.constants import (
    UserRoles, SettingsKeys, TemplatePaths, APIDetection, HTTPStatus,
    ValidationRules, DefaultModelPaths
)
import logging
import uuid

logger = logging.getLogger(__name__)


class BaseOnboardingView(View):
    """Base class for onboarding views with common functionality"""
    
    def get_user_model(self):
        """Get the configured user model"""
        config = get_rbac_config()
        return apps.get_model(config.get(SettingsKeys.GroupRBAC.USER_MODEL, DefaultModelPaths.USER))
    
    def get_password_reset_model(self):
        """Get the configured password reset model"""
        config = get_rbac_config()
        return apps.get_model(config.get(SettingsKeys.GroupRBAC.PASSWORD_RESET_MODEL, DefaultModelPaths.PASSWORD_RESET))
    
    def get_current_user(self, request):
        """Get current user from request"""
        config = get_rbac_config()
        user_getter = config.get(SettingsKeys.GroupRBAC.USER_GETTER)
        if user_getter:
            return user_getter(request)
        return getattr(request, 'user', None)
    
    def is_api_request(self, request):
        """Check if request is from API client"""
        content_type = request.headers.get('Content-Type', '').lower()
        accept = request.headers.get('Accept', '').lower()
        
        api_indicators = [
            request.headers.get('X-Requested-With') == 'XMLHttpRequest',
            'application/json' in content_type,
            'application/json' in accept,
            '/api/' in request.path.lower(),
        ]
        
        return any(api_indicators)
    
    def handle_response(self, request, success, message, data=None, redirect_url=None):
        """Handle response for both web and API requests"""
        if self.is_api_request(request):
            response_data = {'success': success, 'message': message}
            if data:
                response_data.update(data)
            return JsonResponse(response_data, status=200 if success else 400)
        
        # Web request
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        if redirect_url:
            return redirect(redirect_url)
        
        return render(request, 'ldc_dashboard_rbac/onboarding_response.html', {
            'success': success,
            'message': message,
            'data': data
        })


class RegistrationView(BaseOnboardingView):
    """User registration view - creates inactive user pending admin approval"""
    
    def get(self, request):
        """Show registration form"""
        return render(request, 'ldc_dashboard_rbac/registration.html')
    
    def post(self, request):
        """Process registration"""
        try:
            email = request.POST.get('email', '').strip()
            name = request.POST.get('name', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validation
            if not all([email, name, password, confirm_password]):
                return self.handle_response(
                    request, False, 'All fields are required'
                )
            
            if password != confirm_password:
                return self.handle_response(
                    request, False, 'Passwords do not match'
                )
            
            if len(password) < 8:
                return self.handle_response(
                    request, False, 'Password must be at least 8 characters long'
                )
            
            UserModel = self.get_user_model()
            
            # Check if user already exists
            if UserModel.objects.filter(email=email).exists():
                return self.handle_response(
                    request, False, 'User with this email already exists'
                )
            
            # Create user
            with transaction.atomic():
                user = UserModel.objects.create(
                    email=email,
                    name=name,
                    is_active=False,  # Requires admin approval
                    role='user'
                )
                user.set_password(password)
                user.save()
                
                logger.info(f"New user registered: {email} (pending approval)")
                
                # Send notification email to admins (if configured)
                self._notify_admins_of_registration(user)
                
                return self.handle_response(
                    request, True, 
                    'Registration successful! Your account is pending admin approval.',
                    redirect_url='/login/'
                )
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return self.handle_response(
                request, False, 'Registration failed. Please try again.'
            )
    
    def _notify_admins_of_registration(self, user):
        """Send notification to admins about new registration"""
        try:
            UserModel = self.get_user_model()
            admins = UserModel.objects.filter(
                role__in=['admin', 'superadmin'],
                is_active=True
            )
            
            for admin in admins:
                send_email(
                    to_email=admin.email,
                    subject='New User Registration - Approval Required',
                    template='ldc_dashboard_rbac/emails/admin_registration_notification.html',
                    context={
                        'admin_name': admin.name,
                        'new_user_name': user.name,
                        'new_user_email': user.email,
                        'registration_date': user.created_at,
                    }
                )
        except Exception as e:
            logger.error(f"Error notifying admins of registration: {e}")


class AdminRegistrationView(BaseOnboardingView):
    """Admin registration view - admin creates user and sends password setup email"""
    
    def get(self, request):
        """Show admin registration form"""
        current_user = self.get_current_user(request)
        
        # Check if user is admin or superadmin
        if not (is_admin_user(current_user) or is_superadmin_user(current_user)):
            return self.handle_response(
                request, False, 'Access denied. Admin privileges required.'
            )
        
        return render(request, 'ldc_dashboard_rbac/admin_registration.html')
    
    def post(self, request):
        """Process admin registration"""
        try:
            current_user = self.get_current_user(request)
            
            # Check permissions
            if not (is_admin_user(current_user) or is_superadmin_user(current_user)):
                return self.handle_response(
                    request, False, 'Access denied. Admin privileges required.'
                )
            
            email = request.POST.get('email', '').strip()
            name = request.POST.get('name', '').strip()
            role = request.POST.get('role', 'user')
            
            # Validation
            if not all([email, name]):
                return self.handle_response(
                    request, False, 'Email and name are required'
                )
            
            # Role validation
            valid_roles = ['user', 'admin']
            if is_superadmin_user(current_user):
                valid_roles.append('superadmin')
            
            if role not in valid_roles:
                return self.handle_response(
                    request, False, 'Invalid role selected'
                )
            
            # Check if user already exists
            UserModel = self.get_user_model()
            if UserModel.objects.filter(email=email).exists():
                return self.handle_response(
                    request, False, 'User with this email already exists'
                )
            
            # Create user
            with transaction.atomic():
                user = UserModel.objects.create(
                    email=email,
                    name=name,
                    is_active=True,  # Admin-created users are active immediately
                    role=role
                )
                
                # Generate password reset token for initial password setup
                PasswordResetModel = self.get_password_reset_model()
                token = PasswordResetModel.objects.create(
                    user=user,
                    expires_at=timezone.now() + timezone.timedelta(days=7)
                )
                
                # Send password setup email
                self._send_password_setup_email(user, token)
                
                logger.info(f"Admin {current_user.email} created user: {email}")
                
                return self.handle_response(
                    request, True,
                    f'User created successfully! Password setup email sent to {email}.',
                    redirect_url='/admin/users/'
                )
                
        except Exception as e:
            logger.error(f"Admin registration error: {e}")
            return self.handle_response(
                request, False, 'User creation failed. Please try again.'
            )
    
    def _send_password_setup_email(self, user, token):
        """Send password setup email to new user"""
        try:
            reset_url = f"{settings.SITE_URL}/set-password/{token.token}/"
            
            send_email(
                to_email=user.email,
                subject='Set Your Password - Account Created',
                template='ldc_dashboard_rbac/emails/password_setup.html',
                context={
                    'user_name': user.name,
                    'reset_url': reset_url,
                    'expires_in': '7 days',
                }
            )
        except Exception as e:
            logger.error(f"Error sending password setup email: {e}")


class ResetPasswordView(BaseOnboardingView):
    """Password reset view - sends reset email to user"""
    
    def get(self, request):
        """Show password reset form"""
        return render(request, 'ldc_dashboard_rbac/reset_password.html')
    
    def post(self, request):
        """Process password reset request"""
        try:
            email = request.POST.get('email', '').strip()
            
            if not email:
                return self.handle_response(
                    request, False, 'Email is required'
                )
            
            UserModel = self.get_user_model()
            
            try:
                user = UserModel.objects.get(email=email, is_active=True)
            except UserModel.DoesNotExist:
                # Don't reveal if user exists or not for security
                return self.handle_response(
                    request, True,
                    'If an account with this email exists, a password reset link has been sent.'
                )
            
            # Create password reset token
            PasswordResetModel = self.get_password_reset_model()
            
            # Invalidate any existing tokens for this user
            PasswordResetModel.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new token
            token = PasswordResetModel.objects.create(
                user=user,
                expires_at=timezone.now() + timezone.timedelta(hours=24)
            )
            
            # Send reset email
            self._send_reset_email(user, token)
            
            logger.info(f"Password reset requested for: {email}")
            
            return self.handle_response(
                request, True,
                'If an account with this email exists, a password reset link has been sent.'
            )
            
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return self.handle_response(
                request, False, 'Password reset failed. Please try again.'
            )
    
    def _send_reset_email(self, user, token):
        """Send password reset email"""
        try:
            reset_url = f"{settings.SITE_URL}/reset-password/{token.token}/"
            
            send_email(
                to_email=user.email,
                subject='Password Reset Request',
                template='ldc_dashboard_rbac/emails/password_reset.html',
                context={
                    'user_name': user.name,
                    'reset_url': reset_url,
                    'expires_in': '24 hours',
                }
            )
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")


class SetPasswordView(BaseOnboardingView):
    """Set password view - for new users and password reset"""
    
    def get(self, request, token):
        """Show set password form"""
        try:
            PasswordResetModel = self.get_password_reset_model()
            token_obj = PasswordResetModel.objects.get(token=token)
            
            if not token_obj.is_valid():
                return render(request, 'ldc_dashboard_rbac/invalid_token.html', {
                    'error': 'Token has expired or is invalid'
                })
            
            return render(request, 'ldc_dashboard_rbac/set_password.html', {
                'token': token,
                'user': token_obj.user
            })
            
        except PasswordResetModel.DoesNotExist:
            return render(request, 'ldc_dashboard_rbac/invalid_token.html', {
                'error': 'Invalid token'
            })
    
    def post(self, request, token):
        """Process password setting"""
        try:
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validation
            if not all([password, confirm_password]):
                return self.handle_response(
                    request, False, 'All fields are required'
                )
            
            if password != confirm_password:
                return self.handle_response(
                    request, False, 'Passwords do not match'
                )
            
            if len(password) < 8:
                return self.handle_response(
                    request, False, 'Password must be at least 8 characters long'
                )
            
            PasswordResetModel = self.get_password_reset_model()
            
            try:
                token_obj = PasswordResetModel.objects.get(token=token)
            except PasswordResetModel.DoesNotExist:
                return self.handle_response(
                    request, False, 'Invalid token'
                )
            
            if not token_obj.is_valid():
                return self.handle_response(
                    request, False, 'Token has expired or is invalid'
                )
            
            # Set password
            with transaction.atomic():
                user = token_obj.user
                user.set_password(password)
                user.save()
                
                # Mark token as used
                token_obj.is_used = True
                token_obj.save()
                
                logger.info(f"Password set for user: {user.email}")
                
                return self.handle_response(
                    request, True,
                    'Password set successfully! You can now log in.',
                    redirect_url='/login/'
                )
                
        except Exception as e:
            logger.error(f"Set password error: {e}")
            return self.handle_response(
                request, False, 'Password setting failed. Please try again.'
            )


class UserApprovalView(BaseOnboardingView):
    """User approval view - for admins to approve pending users"""
    
    def get(self, request):
        """Show pending users for approval"""
        current_user = self.get_current_user(request)
        
        # Check if user is admin or superadmin
        if not (is_admin_user(current_user) or is_superadmin_user(current_user)):
            return self.handle_response(
                request, False, 'Access denied. Admin privileges required.'
            )
        
        UserModel = self.get_user_model()
        pending_users = UserModel.objects.filter(is_active=False)
        
        return render(request, 'ldc_dashboard_rbac/user_approval.html', {
            'pending_users': pending_users
        })
    
    def post(self, request):
        """Process user approval/rejection"""
        try:
            current_user = self.get_current_user(request)
            
            # Check permissions
            if not (is_admin_user(current_user) or is_superadmin_user(current_user)):
                return self.handle_response(
                    request, False, 'Access denied. Admin privileges required.'
                )
            
            user_id = request.POST.get('user_id')
            action = request.POST.get('action')  # 'approve' or 'reject'
            
            if not all([user_id, action]):
                return self.handle_response(
                    request, False, 'Invalid request'
                )
            
            UserModel = self.get_user_model()
            
            try:
                user = UserModel.objects.get(id=user_id, is_active=False)
            except UserModel.DoesNotExist:
                return self.handle_response(
                    request, False, 'User not found'
                )
            
            if action == 'approve':
                user.is_active = True
                user.save()
                
                # Send approval email
                self._send_approval_email(user)
                
                logger.info(f"User {user.email} approved by {current_user.email}")
                
                return self.handle_response(
                    request, True,
                    f'User {user.name} has been approved and can now log in.',
                    redirect_url='/admin/approvals/'
                )
                
            elif action == 'reject':
                # Send rejection email
                self._send_rejection_email(user)
                
                # Delete the user
                user.delete()
                
                logger.info(f"User {user.email} rejected by {current_user.email}")
                
                return self.handle_response(
                    request, True,
                    f'User {user.name} has been rejected and removed.',
                    redirect_url='/admin/approvals/'
                )
            
            else:
                return self.handle_response(
                    request, False, 'Invalid action'
                )
                
        except Exception as e:
            logger.error(f"User approval error: {e}")
            return self.handle_response(
                request, False, 'User approval failed. Please try again.'
            )
    
    def _send_approval_email(self, user):
        """Send approval email to user"""
        try:
            send_email(
                to_email=user.email,
                subject='Account Approved - Welcome!',
                template='ldc_dashboard_rbac/emails/account_approved.html',
                context={
                    'user_name': user.name,
                    'login_url': f"{settings.SITE_URL}/login/",
                }
            )
        except Exception as e:
            logger.error(f"Error sending approval email: {e}")
    
    def _send_rejection_email(self, user):
        """Send rejection email to user"""
        try:
            send_email(
                to_email=user.email,
                subject='Account Registration - Not Approved',
                template='ldc_dashboard_rbac/emails/account_rejected.html',
                context={
                    'user_name': user.name,
                }
            )
        except Exception as e:
            logger.error(f"Error sending rejection email: {e}")
