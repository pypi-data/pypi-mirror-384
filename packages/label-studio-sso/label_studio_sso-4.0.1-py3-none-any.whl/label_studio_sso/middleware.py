"""
Generic JWT Auto-Login Middleware

Automatically logs in users when they access Label Studio with a valid JWT token
or session cookie.

Supports 3 authentication methods:
1. External JWT (default)
2. Label Studio Native JWT (JWT_SSO_VERIFY_NATIVE_TOKEN=True)
3. External Session Cookie (JWT_SSO_SESSION_VERIFY_URL configured)
"""

import logging
import time
from django.contrib.auth import login
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .backends import JWTAuthenticationBackend, SessionCookieAuthenticationBackend

logger = logging.getLogger(__name__)


class JWTAutoLoginMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log in users via JWT token or session cookie.

    Supports 3 authentication methods:
    1. External JWT: Client generates JWT with shared secret
    2. Label Studio Native JWT: Reuse Label Studio's own JWT tokens
    3. External Session Cookie: Verify client session cookies via API

    Priority order:
    1. JWT token (URL parameter or cookie) - Method 1 or 2
    2. External session cookie - Method 3

    Configuration (in Django settings.py):
        # Method 1 & 2 (JWT)
        JWT_SSO_TOKEN_PARAM: URL parameter name for token (default: 'token')
        JWT_SSO_COOKIE_NAME: Cookie name for JWT token (optional)
        JWT_SSO_VERIFY_NATIVE_TOKEN: Enable native JWT verification (default: False)

        # Method 3 (Session Cookie)
        JWT_SSO_SESSION_VERIFY_URL: Client API URL for session verification
        JWT_SSO_SESSION_VERIFY_SECRET: Shared secret for API authentication
        JWT_SSO_SESSION_COOKIE_NAME: Session cookie name (default: 'sessionid')
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.jwt_backend = JWTAuthenticationBackend()
        self.session_backend = SessionCookieAuthenticationBackend()

    def process_request(self, request):
        # Skip if user is already authenticated
        if request.user.is_authenticated:
            logger.debug(f"User already authenticated: {request.user.email}")
            print(f"[SSO Middleware] User already authenticated: {request.user.email}")
            return

        user = None
        auth_backend = None

        # Priority 1: Check for JWT token (Method 1 or 2)
        token_param = getattr(settings, 'JWT_SSO_TOKEN_PARAM', 'token')
        token = request.GET.get(token_param)

        print(f"[SSO Middleware] Checking for token param '{token_param}' in URL")
        print(f"[SSO Middleware] Token from URL: {token[:20] if token else 'None'}...")

        # If no token in URL, check JWT cookie
        if not token:
            cookie_name = getattr(settings, 'JWT_SSO_COOKIE_NAME', None)
            if cookie_name:
                token = request.COOKIES.get(cookie_name)
                print(f"[SSO Middleware] Checking cookie '{cookie_name}' for JWT token")
                print(f"[SSO Middleware] Token from cookie: {token[:20] if token else 'None'}...")

        if token:
            logger.info("JWT token detected, attempting auto-login")
            print(f"[SSO Middleware] JWT token detected, attempting authentication")

            # Attempt to authenticate with JWT token (Method 1 or 2)
            user = self.jwt_backend.authenticate(request, token=token)
            auth_backend = 'label_studio_sso.backends.JWTAuthenticationBackend'

            print(f"[SSO Middleware] JWT authentication result: {user}")

        # Priority 2: Check for external session cookie (Method 3)
        if not user:
            verify_url = getattr(settings, 'JWT_SSO_SESSION_VERIFY_URL', None)
            if verify_url:
                logger.info("Attempting session cookie authentication")
                print(f"[SSO Middleware] No JWT token, trying session cookie authentication")

                user = self.session_backend.authenticate(request)
                auth_backend = 'label_studio_sso.backends.SessionCookieAuthenticationBackend'

                print(f"[SSO Middleware] Session authentication result: {user}")

        # Log in the user if authentication succeeded
        if user:
            login(request, user, backend=auth_backend)
            # Mark this session as SSO auto-login
            request.session['jwt_auto_login'] = True
            request.session['sso_method'] = 'jwt' if 'JWT' in auth_backend else 'session'
            request.session['last_login'] = time.time()
            logger.info(f"User auto-logged in via {request.session['sso_method']}: {user.email}")
            print(f"[SSO Middleware] User auto-logged in via {request.session['sso_method']}: {user.email}")
        else:
            if token or verify_url:
                logger.warning("SSO authentication failed")
                print(f"[SSO Middleware] SSO authentication FAILED")
