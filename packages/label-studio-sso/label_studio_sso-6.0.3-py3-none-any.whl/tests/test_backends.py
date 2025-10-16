"""
Tests for JWT Authentication Backend
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from label_studio_sso.backends import JWTAuthenticationBackend

User = get_user_model()


@pytest.fixture
def jwt_secret():
    return "test-secret-key"


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def backend():
    return JWTAuthenticationBackend()


@pytest.fixture
def user(db):
    return User.objects.create(email="test@example.com", username="test@example.com")


@pytest.mark.django_db
class TestJWTAuthenticationBackend:
    """Tests for Label Studio Native JWT Authentication"""

    def test_authenticate_without_token(self, backend, request_factory):
        """Test authentication without providing a token"""
        request = request_factory.get("/")
        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_authenticate_with_drf_token_header(self, backend, request_factory):
        """Test that DRF Token authentication is bypassed"""
        request = request_factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = "Token drf-token-here"

        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_get_user(self, backend, user):
        """Test get_user method"""
        retrieved_user = backend.get_user(user.id)
        assert retrieved_user == user

        # Test with non-existent user ID
        assert backend.get_user(99999) is None

    def test_authenticate_with_native_jwt(self, request_factory, user):
        """Test authentication with Label Studio native JWT token"""
        backend = JWTAuthenticationBackend()

        # Create native JWT token with Label Studio SECRET_KEY
        labelstudio_secret = "labelstudio-secret-key"
        token = jwt.encode(
            {
                "user_id": user.id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            labelstudio_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.email == user.email

    def test_authenticate_native_jwt_missing_user_id(self, request_factory):
        """Test native JWT without user_id claim"""
        backend = JWTAuthenticationBackend()

        labelstudio_secret = "labelstudio-secret-key"
        token = jwt.encode(
            {
                "email": "test@example.com",  # No user_id
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            labelstudio_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_native_jwt_nonexistent_user(self, request_factory):
        """Test native JWT with non-existent user ID"""
        backend = JWTAuthenticationBackend()

        labelstudio_secret = "labelstudio-secret-key"
        token = jwt.encode(
            {
                "user_id": 99999,  # Non-existent user
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            labelstudio_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_with_expired_token(self, backend, request_factory, user):
        """Test authentication with an expired JWT token"""
        labelstudio_secret = "labelstudio-secret-key"

        # Create expired token
        token = jwt.encode(
            {
                "user_id": user.id,
                "iat": datetime.utcnow() - timedelta(minutes=20),
                "exp": datetime.utcnow() - timedelta(minutes=10),
            },
            labelstudio_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_with_invalid_signature(self, backend, request_factory, user):
        """Test authentication with invalid token signature"""
        labelstudio_secret = "labelstudio-secret-key"

        # Create token with wrong secret
        token = jwt.encode(
            {
                "user_id": user.id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            "wrong-secret",
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None
