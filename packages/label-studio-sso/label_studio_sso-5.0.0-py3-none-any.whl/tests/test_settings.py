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
JWT_SSO_SECRET = "test-jwt-secret"
JWT_SSO_ALGORITHM = "HS256"
JWT_SSO_TOKEN_PARAM = "token"
JWT_SSO_EMAIL_CLAIM = "email"
JWT_SSO_USERNAME_CLAIM = "username"
JWT_SSO_FIRST_NAME_CLAIM = "first_name"
JWT_SSO_LAST_NAME_CLAIM = "last_name"
JWT_SSO_AUTO_CREATE_USERS = True

USE_TZ = True
