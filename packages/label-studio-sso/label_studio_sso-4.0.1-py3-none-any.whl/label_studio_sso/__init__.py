"""
Label Studio SSO - Generic JWT Authentication

Universal JWT-based SSO authentication for Label Studio.
Works with any external system that can issue JWT tokens.

Provides:
- JWT URL parameter authentication
- Configurable JWT claims mapping
- Auto-user creation (optional)
- Simple integration with any JWT-based system
"""

__version__ = '3.0.0'
__author__ = 'Label Studio SSO Team'
__license__ = 'MIT'

default_app_config = 'label_studio_sso.apps.LabelStudioSsoConfig'

# Do not import here - causes AppRegistryNotReady error
# Import backends and middleware directly in settings.py instead
__all__ = [
    'JWTAuthenticationBackend',
    'JWTAutoLoginMiddleware',
]
