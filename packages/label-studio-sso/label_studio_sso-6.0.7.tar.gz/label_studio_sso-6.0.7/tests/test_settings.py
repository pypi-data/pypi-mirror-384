"""
Django settings for label-studio-sso tests
"""

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "label_studio_sso",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "label_studio_sso.middleware.JWTAutoLoginMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "label_studio_sso.backends.JWTAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]

SECRET_KEY = "test-secret-key-for-django"

# Method 2 (Native JWT) Configuration
JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
JWT_SSO_TOKEN_PARAM = "token"
JWT_SSO_COOKIE_NAME = None

# API Configuration
SSO_TOKEN_EXPIRY = 600
SSO_AUTO_CREATE_USERS = True

USE_TZ = True
