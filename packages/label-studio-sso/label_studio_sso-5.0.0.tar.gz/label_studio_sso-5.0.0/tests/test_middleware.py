"""
Tests for JWT Auto-Login Middleware
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import jwt
import pytest
import responses
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from label_studio_sso.middleware import JWTAutoLoginMiddleware

User = get_user_model()


@pytest.fixture
def jwt_secret():
    return "test-secret-key"


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def get_response():
    """Mock get_response callable"""
    return Mock(return_value=Mock(status_code=200))


@pytest.fixture
def middleware(get_response):
    return JWTAutoLoginMiddleware(get_response)


@pytest.fixture
def user(db):
    return User.objects.create(email="test@example.com", username="test@example.com")


@pytest.mark.django_db
class TestJWTAutoLoginMiddleware:

    def test_auto_login_with_valid_token(
        self, middleware, request_factory, user, jwt_secret, get_response
    ):
        """Test auto-login with a valid JWT token in URL"""
        # Create valid token
        token = jwt.encode(
            {
                "email": "test@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get(f"/?token={token}")
        request.user = MagicMock(is_authenticated=False)
        request.session = SessionStore()
        request.session.create()

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = None
            with patch("label_studio_sso.middleware.login") as mock_login:
                response = middleware(request)

                # Verify login was called
                assert mock_login.called
                assert mock_login.call_args[0][1] == user

    def test_skip_if_already_authenticated(self, middleware, request_factory, user, get_response):
        """Test middleware skips processing if user is already authenticated"""
        request = request_factory.get("/?token=some-token")
        request.user = user  # Real authenticated user
        request.session = SessionStore()
        request.session.create()

        with patch("label_studio_sso.middleware.login") as mock_login:
            response = middleware(request)

            # Verify login was NOT called
            assert not mock_login.called

    def test_skip_if_no_token(self, middleware, request_factory, get_response):
        """Test middleware skips processing if no token in URL"""
        request = request_factory.get("/")
        request.user = MagicMock(is_authenticated=False)

        with patch("label_studio_sso.middleware.login") as mock_login:
            response = middleware(request)

            # Verify login was NOT called
            assert not mock_login.called

    def test_continue_on_authentication_failure(
        self, middleware, request_factory, jwt_secret, get_response
    ):
        """Test middleware continues processing even if authentication fails"""
        # Create token for non-existent user
        token = jwt.encode(
            {
                "email": "nonexistent@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get(f"/?token={token}")
        request.user = MagicMock(is_authenticated=False)
        request.session = SessionStore()
        request.session.create()

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = False  # Don't auto-create, expect failure
            with patch("label_studio_sso.middleware.login") as mock_login:
                response = middleware(request)

                # Verify login was NOT called
                assert not mock_login.called
                # Verify response was still generated
                assert get_response.called

    def test_invalid_token_handling(self, middleware, request_factory, get_response):
        """Test handling of invalid/malformed JWT tokens"""
        request = request_factory.get("/?token=invalid-token-format")
        request.user = MagicMock(is_authenticated=False)

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_SECRET = "test-secret"
            with patch("label_studio_sso.middleware.login") as mock_login:
                response = middleware(request)

                # Verify login was NOT called
                assert not mock_login.called
                # Verify response was still generated
                assert get_response.called

    def test_auto_login_with_cookie_token(
        self, middleware, request_factory, user, jwt_secret, get_response
    ):
        """Test auto-login with a valid JWT token in Cookie"""
        # Create valid token
        token = jwt.encode(
            {
                "email": "test@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        # Request without URL token, but with cookie
        request = request_factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        request.session = SessionStore()
        request.session.create()
        request.COOKIES = {"jwt_auth_token": token}

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = "jwt_auth_token"  # Enable cookie auth
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True

            with patch("label_studio_sso.middleware.settings", mock_settings):
                with patch("label_studio_sso.middleware.login") as mock_login:
                    response = middleware(request)

                    # Verify login was called
                    assert mock_login.called
                    assert mock_login.call_args[0][1] == user

    def test_cookie_priority_over_url_token(
        self, middleware, request_factory, user, jwt_secret, get_response
    ):
        """Test that cookie token takes priority over URL token (more secure)"""
        # Create valid tokens
        url_token = jwt.encode(
            {
                "email": "url@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        cookie_token = jwt.encode(
            {
                "email": "cookie@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        # Request with both URL and cookie tokens
        request = request_factory.get(f"/?token={url_token}")
        request.user = MagicMock(is_authenticated=False)
        request.session = SessionStore()
        request.session.create()
        request.COOKIES = {"jwt_auth_token": cookie_token}

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = "jwt_auth_token"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True

            with patch("label_studio_sso.middleware.settings", mock_settings):
                # The backend should receive the cookie token (higher priority)
                with patch.object(
                    middleware.jwt_backend,
                    "authenticate",
                    wraps=middleware.jwt_backend.authenticate,
                ) as mock_auth:
                    response = middleware(request)

                    # Verify authenticate was called with cookie token
                    assert mock_auth.called
                    # The token argument should be the cookie token (not URL token)
                    call_args = mock_auth.call_args
                    assert call_args[1]["token"] == cookie_token

    def test_cookie_fallback_when_no_url_token(
        self, middleware, request_factory, user, jwt_secret, get_response
    ):
        """Test that cookie token is used when URL token is not present"""
        # Create valid cookie token
        cookie_token = jwt.encode(
            {
                "email": "test@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        # Request without URL token, only cookie
        request = request_factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        request.session = SessionStore()
        request.session.create()
        request.COOKIES = {"jwt_auth_token": cookie_token}

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = "jwt_auth_token"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True

            with patch("label_studio_sso.middleware.settings", mock_settings):
                with patch.object(
                    middleware.jwt_backend,
                    "authenticate",
                    wraps=middleware.jwt_backend.authenticate,
                ) as mock_auth:
                    response = middleware(request)

                    # Verify authenticate was called with cookie token
                    assert mock_auth.called
                    call_args = mock_auth.call_args
                    assert call_args[1]["token"] == cookie_token
