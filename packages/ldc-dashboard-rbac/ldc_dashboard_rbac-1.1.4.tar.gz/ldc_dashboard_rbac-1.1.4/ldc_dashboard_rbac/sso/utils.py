import logging
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured

# Use standard Python logging
logger = logging.getLogger(__name__)

# Define default configuration
DEFAULT_SSO_CONFIG = {
    'GOOGLE_OAUTH_SCOPES': ['openid', 'email', 'profile'],
    'SSO_CALLBACK_URL_NAME': 'dashboard_sso:google_callback',
    'SSO_LOGIN_URL_NAME': 'login',
    'SSO_SUCCESS_REDIRECT_URL_NAME': 'home'
}

def get_sso_config():
    """Get SSO configuration with defaults"""
    user_config = getattr(settings, 'DASHBOARD_SSO_CONFIG', {})
    config = DEFAULT_SSO_CONFIG.copy()
    config.update(user_config)
    return config

def get_google_auth_flow(request):
    """Create Google OAuth flow object"""
    sso_config = get_sso_config()
    try:
        if not sso_config.get('GOOGLE_OAUTH_CLIENT_ID') or not sso_config.get('GOOGLE_OAUTH_CLIENT_SECRET'):
            raise ImproperlyConfigured("Google OAuth credentials are not configured in DASHBOARD_SSO_CONFIG.")

        callback_url_name = sso_config.get('SSO_CALLBACK_URL_NAME')
        
        # Check if there's an override redirect URI first
        override_uri = sso_config.get('OVERRIDE_REDIRECT_URI')
        if override_uri:
            redirect_uri = override_uri
        else:
            # Fall back to Django's auto-generated URI
            redirect_uri = request.build_absolute_uri(reverse(callback_url_name))

        flow = Flow.from_client_config({
            "web": {
                "client_id": sso_config.get('GOOGLE_OAUTH_CLIENT_ID'),
                "client_secret": sso_config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }, scopes=sso_config.get('GOOGLE_OAUTH_SCOPES'))
        
        flow.redirect_uri = redirect_uri
        return flow, None
    except Exception as e:
        logger.error(f"Error creating Google auth flow: {str(e)}")
        return None, f"Error initializing Google authentication: {str(e)}"

def initiate_google_sso(request):
    """Initiate Google SSO flow"""
    try:
        flow, error = get_google_auth_flow(request)
        if error:
            return {'success': False, 'message': error}

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        request.session['google_oauth_state'] = state
        return {
            'success': True,
            'response_data': {'authorization_url': authorization_url}
        }
    except Exception as e:
        logger.error(f"Error initiating Google SSO: {str(e)}")
        return {'success': False, 'message': f'Error initiating Google SSO: {str(e)}'}

def handle_google_callback(request):
    """Handle Google OAuth callback"""
    sso_config = get_sso_config()
    try:
        state = request.GET.get('state')
        stored_state = request.session.get('google_oauth_state')

        if not state or state != stored_state:
            return {'success': False, 'message': 'Invalid state parameter.'}

        code = request.GET.get('code')
        if not code:
            return {'success': False, 'message': 'No authorization code received.'}

        flow, flow_error = get_google_auth_flow(request)
        if flow_error:
            return {'success': False, 'message': flow_error}

        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        try:
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                sso_config.get('GOOGLE_OAUTH_CLIENT_ID'),
                clock_skew_in_seconds=60
            )
        except Exception as token_error:
            logger.error(f"ID token verification failed: {str(token_error)}")
            return {'success': False, 'message': 'Token verification failed.'}

        email = id_info.get('email')
        if not email:
            return {'success': False, 'message': 'Unable to retrieve email from Google.'}

        User = get_user_model()
        user = User.objects.filter(email=email, is_active=True).first()

        if not user:
            return {'success': False, 'message': f'No active account found for email: {email}. Please contact an administrator.'}
        
        # Dynamically import and call the post-login hook
        post_login_function_path = sso_config.get('SSO_POST_LOGIN_FUNCTION')
        if not post_login_function_path:
            raise ImproperlyConfigured("DASHBOARD_SSO_CONFIG must define 'SSO_POST_LOGIN_FUNCTION'")

        post_login_function = import_string(post_login_function_path)
        result = post_login_function(request, user, id_info)

        if not result.get('success'):
            return {'success': False, 'message': result.get('message', 'Post-login processing failed.')}

        if 'google_oauth_state' in request.session:
            del request.session['google_oauth_state']

        return {
            'success': True,
            'response_data': {'user': result.get('user_details')}
        }
    except Exception as e:
        logger.error(f"Error handling Google callback: {str(e)}")
        return {'success': False, 'message': 'Authentication failed due to a server error.'}