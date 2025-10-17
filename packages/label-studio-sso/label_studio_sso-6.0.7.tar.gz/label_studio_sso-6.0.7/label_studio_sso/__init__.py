"""
Label Studio SSO - Native JWT Authentication

Native JWT-based SSO authentication for Label Studio.
Label Studio issues JWT tokens via API for seamless user authentication.

Provides:
- Native JWT authentication using Label Studio's SECRET_KEY
- Cookie and URL parameter authentication
- Secure API token-based token issuance
- Simple and secure SSO integration
"""

__version__ = "6.0.0"
__author__ = "Label Studio SSO Team"
__license__ = "MIT"

default_app_config = "label_studio_sso.apps.LabelStudioSsoConfig"

# Do not import here - causes AppRegistryNotReady error
# Import backends and middleware directly in settings.py instead
__all__ = [
    "JWTAuthenticationBackend",
    "JWTAutoLoginMiddleware",
]
