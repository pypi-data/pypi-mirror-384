"""
Tests for JWT Authentication Backend
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import jwt
import pytest
import responses
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

    def test_authenticate_with_valid_token(self, backend, request_factory, user, jwt_secret):
        """Test authentication with a valid JWT token"""
        # Create valid JWT token
        token = jwt.encode(
            {
                "email": "test@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False  # Use external JWT
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is not None
        assert authenticated_user.email == "test@example.com"

    def test_authenticate_with_expired_token(self, backend, request_factory, user, jwt_secret):
        """Test authentication with an expired JWT token"""
        # Create expired token
        token = jwt.encode(
            {
                "email": "test@example.com",
                "iat": datetime.utcnow() - timedelta(minutes=20),
                "exp": datetime.utcnow() - timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_with_invalid_signature(self, backend, request_factory, user, jwt_secret):
        """Test authentication with invalid token signature"""
        # Create token with wrong secret
        token = jwt.encode(
            {
                "email": "test@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            "wrong-secret",
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_with_nonexistent_user(self, backend, request_factory, jwt_secret):
        """Test authentication when user doesn't exist in Label Studio"""
        token = jwt.encode(
            {
                "email": "nonexistent@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = False  # Don't auto-create
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_without_token(self, backend, request_factory):
        """Test authentication without providing a token"""
        request = request_factory.get("/")
        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_authenticate_with_token_missing_email(self, backend, request_factory, jwt_secret):
        """Test authentication with token that doesn't contain email"""
        token = jwt.encode(
            {
                "username": "testuser",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_get_user(self, backend, user):
        """Test get_user method"""
        retrieved_user = backend.get_user(user.id)
        assert retrieved_user == user

        # Test with non-existent user ID
        assert backend.get_user(99999) is None

    def test_authenticate_with_drf_token_header(self, backend, request_factory):
        """Test that DRF Token authentication is bypassed"""
        request = request_factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = "Token drf-token-here"

        authenticated_user = backend.authenticate(request)

        assert authenticated_user is None

    def test_authenticate_without_jwt_secret(self, backend, request_factory, jwt_secret):
        """Test authentication when JWT_SSO_SECRET is not configured"""
        token = jwt.encode(
            {
                "email": "test@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = None  # Secret not configured
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_with_no_email_no_username(self, backend, request_factory, jwt_secret):
        """Test authentication with token missing both email and username"""
        token = jwt.encode(
            {
                "sub": "some-id",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None

    def test_authenticate_with_username_only(self, backend, request_factory, jwt_secret, db):
        """Test authentication with username but no email in JWT"""
        # Create user with username
        user = User.objects.create(email="usernametest@example.com", username="testuser")

        token = jwt.encode(
            {
                "username": "testuser",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"

    def test_authenticate_with_email_prefix_search(self, backend, request_factory, jwt_secret, db):
        """Test authentication by email prefix when username provided but no email"""
        # Create user with email starting with username
        user = User.objects.create(email="john@company.com", username="john@company.com")

        token = jwt.encode(
            {
                "username": "john",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is not None
        assert authenticated_user.email == "john@company.com"

    def test_authenticate_with_multiple_email_prefix_matches(
        self, backend, request_factory, jwt_secret, db
    ):
        """Test authentication when multiple users match email prefix"""
        # Create multiple users with same prefix
        User.objects.create(email="admin@company.com", username="admin1")
        User.objects.create(email="admin@another.com", username="admin2")

        token = jwt.encode(
            {
                "username": "admin",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            authenticated_user = backend.authenticate(request, token=token)

        # Should return None when multiple matches found
        assert authenticated_user is None

    def test_user_info_update_last_name(self, backend, request_factory, user, jwt_secret):
        """Test that user's last_name is updated from JWT"""
        token = jwt.encode(
            {
                "email": "test@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            jwt_secret,
            algorithm="HS256",
        )

        request = request_factory.get("/")

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = "HS256"
            mock_settings.JWT_SSO_EMAIL_CLAIM = "email"
            mock_settings.JWT_SSO_USERNAME_CLAIM = "username"
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True
            mock_settings.JWT_SSO_FIRST_NAME_CLAIM = "first_name"
            mock_settings.JWT_SSO_LAST_NAME_CLAIM = "last_name"
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user.first_name == "John"
        assert authenticated_user.last_name == "Doe"

        # Verify in database
        user.refresh_from_db()
        assert user.first_name == "John"
        assert user.last_name == "Doe"


@pytest.mark.django_db
class TestLabelStudioNativeJWT:
    """Tests for Method 2: Label Studio Native JWT Authentication"""

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
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = True
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
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = True
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
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = True
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is None
