"""
DRF SessionAuthentication for Label Studio SSO

Provides Django REST Framework authentication using Django sessions created by JWTAutoLoginMiddleware.
"""

from rest_framework.authentication import SessionAuthentication


class JWTSSOSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication for DRF API endpoints.

    Uses Django sessions created by JWTAutoLoginMiddleware.
    This allows API calls to authenticate using the session cookie
    after JWT auto-login has been performed.

    CSRF is disabled for API calls from iframe to avoid cross-origin issues.
    """

    def enforce_csrf(self, request):
        """
        Disable CSRF check for session authentication.

        This is necessary for iframe embedding where CSRF tokens
        cannot be easily managed across origins.
        """
        return  # Skip CSRF check

    def authenticate(self, request):
        """
        Authenticate using Django session.

        Returns (user, None) if authenticated via session, or None otherwise.
        """
        # Call parent to get user from session
        user_auth = super().authenticate(request)

        if user_auth:
            return user_auth

        return None
