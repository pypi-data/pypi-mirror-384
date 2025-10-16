"""
Generic JWT Auto-Login Middleware

Automatically logs in users when they access Label Studio with a valid JWT token.

Supports 2 authentication methods:
1. External JWT (default)
2. Label Studio Native JWT (JWT_SSO_VERIFY_NATIVE_TOKEN=True)

Authentication Priority:
1. Django Session (ls_sessionid) - Fast, no JWT verification needed
2. JWT Cookie (JWT_SSO_COOKIE_NAME) - Secure, HttpOnly cookie
3. JWT URL Parameter (JWT_SSO_TOKEN_PARAM) - Backward compatibility
"""

import logging
import time

from django.conf import settings
from django.contrib.auth import login
from django.utils.deprecation import MiddlewareMixin

from .backends import JWTAuthenticationBackend

logger = logging.getLogger(__name__)


class JWTAutoLoginMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log in users via JWT token.

    Supports 2 authentication methods:
    1. External JWT: Client generates JWT with shared secret
    2. Label Studio Native JWT: Reuse Label Studio's own JWT tokens

    Authentication Priority:
    1. Django Session (checked by AuthenticationMiddleware before this)
       - If user already authenticated, skip JWT verification (performance optimization)
    2. JWT Cookie (JWT_SSO_COOKIE_NAME) - Preferred, more secure
       - HttpOnly cookie, not visible to JavaScript
       - Not exposed in URLs, browser history, or logs
    3. JWT URL Parameter (JWT_SSO_TOKEN_PARAM) - Backward compatibility
       - Less secure, exposed in URLs
       - Kept for legacy systems

    Configuration (in Django settings.py):
        JWT_SSO_COOKIE_NAME: Cookie name for JWT token (recommended: 'ls_auth_token')
        JWT_SSO_TOKEN_PARAM: URL parameter name for token (default: 'token', legacy)
        JWT_SSO_VERIFY_NATIVE_TOKEN: Enable native JWT verification (default: False)

    Example Configuration:
        # Recommended setup (Cookie-based SSO)
        JWT_SSO_COOKIE_NAME = 'ls_auth_token'  # Initial authentication token
        SESSION_COOKIE_NAME = 'ls_sessionid'   # Persistent session after login

        # Flow:
        # 1. Client sets ls_auth_token cookie (10 min expiry)
        # 2. First request: JWT verified, session created (ls_sessionid)
        # 3. Subsequent requests: Session used (fast, no JWT verification)
        # 4. Session expires: Fall back to ls_auth_token
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.jwt_backend = JWTAuthenticationBackend()

    def process_request(self, request):
        # Skip if user is already authenticated via Django session
        if request.user.is_authenticated:
            logger.debug(f"User already authenticated via session: {request.user.email}")
            print(f"[SSO Middleware] User already authenticated via session: {request.user.email}")
            return

        user = None
        auth_backend = None

        # Priority 1: Check for JWT token in Cookie (preferred, more secure)
        token = None
        cookie_name = getattr(settings, "JWT_SSO_COOKIE_NAME", None)
        if cookie_name:
            token = request.COOKIES.get(cookie_name)
            if token:
                logger.info(f"JWT token found in cookie: {cookie_name}")
                print(f"[SSO Middleware] JWT token found in cookie '{cookie_name}'")
                print(f"[SSO Middleware] Token from cookie: {token[:20]}...")

        # Priority 2: Check for JWT token in URL parameter (fallback, backward compatibility)
        if not token:
            token_param = getattr(settings, "JWT_SSO_TOKEN_PARAM", "token")
            token = request.GET.get(token_param)
            if token:
                logger.info(f"JWT token found in URL parameter: {token_param}")
                print(f"[SSO Middleware] JWT token found in URL param '{token_param}'")
                print(f"[SSO Middleware] Token from URL: {token[:20]}...")

        if token:
            logger.info("JWT token detected, attempting auto-login")
            print(f"[SSO Middleware] JWT token detected, attempting authentication")

            # Attempt to authenticate with JWT token (Method 1 or 2)
            user = self.jwt_backend.authenticate(request, token=token)
            auth_backend = "label_studio_sso.backends.JWTAuthenticationBackend"

            print(f"[SSO Middleware] JWT authentication result: {user}")

        # Log in the user if authentication succeeded
        if user:
            login(request, user, backend=auth_backend)
            # Mark this session as SSO auto-login
            request.session["jwt_auto_login"] = True
            request.session["sso_method"] = "jwt"
            request.session["last_login"] = time.time()
            logger.info(f"User auto-logged in via JWT: {user.email}")
            print(f"[SSO Middleware] User auto-logged in via JWT: {user.email}")
        else:
            if token:
                logger.warning("JWT authentication failed")
                print(f"[SSO Middleware] JWT authentication FAILED")

    def process_response(self, request, response):
        """
        Clean up expired JWT token cookie from response.

        If JWT token was expired during authentication, delete the cookie
        to prevent repeated authentication attempts with invalid token.
        """
        if getattr(request, "_sso_jwt_expired", False):
            cookie_name = getattr(settings, "JWT_SSO_COOKIE_NAME", None)
            if cookie_name:
                # Delete expired token cookie
                response.delete_cookie(
                    cookie_name, path=getattr(settings, "JWT_SSO_COOKIE_PATH", "/label-studio")
                )
                logger.info(f"Deleted expired JWT token cookie: {cookie_name}")
                print(f"[SSO Middleware] Deleted expired token cookie: {cookie_name}")

        return response
