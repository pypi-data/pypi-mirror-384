"""
Simple unit tests for JWT SSO
"""

from datetime import datetime, timedelta

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from label_studio_sso.backends import JWTAuthenticationBackend
from label_studio_sso.middleware import JWTAutoLoginMiddleware

User = get_user_model()


@pytest.mark.django_db
class TestJWTBackend:
    def test_import(self):
        """Test that backend can be imported"""
        backend = JWTAuthenticationBackend()
        assert backend is not None

    def test_authenticate_with_valid_token(self):
        """Test authentication with valid token (Native JWT)"""
        from unittest.mock import patch

        backend = JWTAuthenticationBackend()

        # Create user
        user = User.objects.create(email="test@example.com", username="testuser")

        labelstudio_secret = "labelstudio-secret-key"

        # Create token with user_id
        token = jwt.encode(
            {
                "user_id": user.id,
                "email": "test@example.com",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            labelstudio_secret,
            algorithm="HS256",
        )

        # Create request
        factory = RequestFactory()
        request = factory.get("/")

        # Authenticate
        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is not None
        assert authenticated_user.email == "test@example.com"
        assert authenticated_user.id == user.id

    def test_authenticate_with_invalid_token(self):
        """Test authentication with invalid token"""
        backend = JWTAuthenticationBackend()

        factory = RequestFactory()
        request = factory.get("/")

        # Authenticate with invalid token
        authenticated_user = backend.authenticate(request, token="invalid-token")

        assert authenticated_user is None


@pytest.mark.django_db
class TestJWTMiddleware:
    def test_import(self):
        """Test that middleware can be imported"""

        def get_response(request):
            return None

        middleware = JWTAutoLoginMiddleware(get_response)
        assert middleware is not None
