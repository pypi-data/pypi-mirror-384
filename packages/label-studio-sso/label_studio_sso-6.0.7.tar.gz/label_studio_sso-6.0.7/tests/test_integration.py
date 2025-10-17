"""
Integration tests for label-studio-sso (Method 2: Native JWT)
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

User = get_user_model()


class TestIntegration:
    """Integration tests for the complete SSO flow using Native JWT"""

    def test_complete_sso_flow(self, db):
        """Test complete SSO authentication flow with Native JWT"""
        labelstudio_secret = "labelstudio-secret-key"

        # 1. Create user first (in real scenario, created via API)
        user = User.objects.create(
            email="integration@example.com",
            username="integrationuser",
        )

        # 2. Label Studio generates JWT token (simulating /api/sso/token)
        user_data = {
            "user_id": user.id,
            "email": user.email,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=10),
        }
        token = jwt.encode(user_data, labelstudio_secret, algorithm="HS256")

        # 3. User visits Label Studio with token in URL
        factory = RequestFactory()
        request = factory.get("/", {"token": token})
        request.user = AnonymousUser()
        request.session = SessionStore()
        request.session.create()

        # 4. Middleware processes the request
        from label_studio_sso.middleware import JWTAutoLoginMiddleware

        def get_response(request):
            return None

        middleware = JWTAutoLoginMiddleware(get_response)

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = None
            middleware.process_request(request)

        # 5. User should be authenticated
        assert request.user.is_authenticated
        assert request.user.email == "integration@example.com"
        assert request.user.username == "integrationuser"

    def test_multiple_logins_same_user(self, db):
        """Test multiple login attempts for the same user"""
        labelstudio_secret = "labelstudio-secret-key"

        # Create user
        user = User.objects.create(
            email="repeat@example.com",
            username="repeatuser",
        )

        user_data = {
            "user_id": user.id,
            "email": user.email,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=10),
        }

        # First login
        token1 = jwt.encode(user_data, labelstudio_secret, algorithm="HS256")
        factory = RequestFactory()
        request1 = factory.get("/", {"token": token1})
        request1.user = AnonymousUser()
        request1.session = SessionStore()
        request1.session.create()

        from label_studio_sso.middleware import JWTAutoLoginMiddleware

        def get_response(request):
            return None

        middleware = JWTAutoLoginMiddleware(get_response)

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = None
            middleware.process_request(request1)

        user1_id = request1.user.id

        # Second login (new token, same user)
        token2 = jwt.encode(user_data, labelstudio_secret, algorithm="HS256")
        request2 = factory.get("/", {"token": token2})
        request2.user = AnonymousUser()
        request2.session = SessionStore()
        request2.session.create()

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = None
            middleware.process_request(request2)

        # Should be the same user
        assert request2.user.id == user1_id

        # Should only have one user in database
        assert User.objects.filter(email="repeat@example.com").count() == 1

    def test_backend_without_middleware(self, db):
        """Test using backend directly without middleware"""
        from label_studio_sso.backends import JWTAuthenticationBackend

        labelstudio_secret = "labelstudio-secret-key"

        # Create user
        user = User.objects.create(
            email="backend@example.com",
            username="backenduser",
        )

        # Generate token
        token = jwt.encode(
            {
                "user_id": user.id,
                "email": user.email,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            labelstudio_secret,
            algorithm="HS256",
        )

        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        backend = JWTAuthenticationBackend()

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            authenticated_user = backend.authenticate(request, token=token)

        assert authenticated_user is not None
        assert authenticated_user.email == "backend@example.com"
        assert authenticated_user.id == user.id

    def test_token_with_cookie(self, db):
        """Test authentication with JWT in cookie (recommended approach)"""
        from label_studio_sso.middleware import JWTAutoLoginMiddleware

        labelstudio_secret = "labelstudio-secret-key"

        # Create user
        user = User.objects.create(
            email="cookie@example.com",
            username="cookieuser",
        )

        # Generate token
        token = jwt.encode(
            {
                "user_id": user.id,
                "email": user.email,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
            },
            labelstudio_secret,
            algorithm="HS256",
        )

        factory = RequestFactory()
        request = factory.get("/")  # No token in URL
        request.user = AnonymousUser()
        request.session = SessionStore()
        request.session.create()
        request.COOKIES = {"ls_auth_token": token}

        def get_response(request):
            return None

        middleware = JWTAutoLoginMiddleware(get_response)

        with patch("label_studio_sso.backends.settings") as mock_settings:
            mock_settings.JWT_SSO_NATIVE_USER_ID_CLAIM = "user_id"
            mock_settings.SECRET_KEY = labelstudio_secret
            mock_settings.JWT_SSO_TOKEN_PARAM = "token"
            mock_settings.JWT_SSO_COOKIE_NAME = "ls_auth_token"
            with patch("label_studio_sso.middleware.settings", mock_settings):
                middleware.process_request(request)

        # User should be authenticated via cookie
        assert request.user.is_authenticated
        assert request.user.email == "cookie@example.com"
