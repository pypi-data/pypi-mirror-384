"""
DRF Authentication Classes for JWT SSO

Provides CSRF-exempt session authentication for iframe/embedded scenarios.
"""

from rest_framework.authentication import SessionAuthentication


class JWTSSOSessionAuthentication(SessionAuthentication):
    """
    Session authentication that skips CSRF verification.

    Used for JWT SSO scenarios where Label Studio is embedded in iframe.
    The JWT token provides authentication, and CSRF protection is not needed
    for API calls from embedded contexts.

    This allows the frontend to make API calls without CSRF tokens when
    authenticated via JWT SSO.
    """

    def enforce_csrf(self, request):
        """
        Skip CSRF check for JWT SSO authenticated requests.

        Returns:
            None - effectively disabling CSRF enforcement
        """
        return  # Do not perform CSRF check
