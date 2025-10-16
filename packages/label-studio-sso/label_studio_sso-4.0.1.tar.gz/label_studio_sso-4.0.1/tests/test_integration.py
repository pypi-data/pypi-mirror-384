"""
Integration tests for label-studio-sso
"""
import pytest
import jwt
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore

User = get_user_model()


class TestIntegration:
    """Integration tests for the complete SSO flow"""

    def test_complete_sso_flow(self, jwt_secret, db):
        """Test complete SSO authentication flow"""
        # 1. External system generates JWT token
        user_data = {
            'email': 'integration@example.com',
            'username': 'integrationuser',
            'first_name': 'Integration',
            'last_name': 'Test',
            'exp': datetime.utcnow() + timedelta(minutes=10)
        }
        token = jwt.encode(user_data, jwt_secret, algorithm='HS256')

        # 2. User visits Label Studio with token in URL
        factory = RequestFactory()
        request = factory.get('/', {'token': token})
        request.user = AnonymousUser()
        request.session = SessionStore()
        request.session.create()

        # 3. Middleware processes the request
        from label_studio_sso.middleware import JWTAutoLoginMiddleware

        def get_response(request):
            return None

        middleware = JWTAutoLoginMiddleware(get_response)
        middleware.process_request(request)

        # 4. User should be authenticated
        assert request.user.is_authenticated
        assert request.user.email == 'integration@example.com'
        assert request.user.username == 'integrationuser'

        # 5. User should exist in database
        user = User.objects.get(email='integration@example.com')
        assert user is not None
        assert user.first_name == 'Integration'
        assert user.last_name == 'Test'

    def test_multiple_logins_same_user(self, jwt_secret, db):
        """Test multiple login attempts for the same user"""
        user_data = {
            'email': 'repeat@example.com',
            'username': 'repeatuser',
            'exp': datetime.utcnow() + timedelta(minutes=10)
        }

        # First login
        token1 = jwt.encode(user_data, jwt_secret, algorithm='HS256')
        factory = RequestFactory()
        request1 = factory.get('/', {'token': token1})
        request1.user = AnonymousUser()
        request1.session = SessionStore()
        request1.session.create()

        from label_studio_sso.middleware import JWTAutoLoginMiddleware

        def get_response(request):
            return None

        middleware = JWTAutoLoginMiddleware(get_response)
        middleware.process_request(request1)

        user1_id = request1.user.id

        # Second login (new token, same user)
        token2 = jwt.encode(user_data, jwt_secret, algorithm='HS256')
        request2 = factory.get('/', {'token': token2})
        request2.user = AnonymousUser()
        request2.session = SessionStore()
        request2.session.create()

        middleware.process_request(request2)

        # Should be the same user
        assert request2.user.id == user1_id

        # Should only have one user in database
        assert User.objects.filter(email='repeat@example.com').count() == 1

    def test_backend_without_middleware(self, valid_jwt_token, user_data, jwt_secret, db):
        """Test using backend directly without middleware"""
        from label_studio_sso.backends import JWTAuthenticationBackend
        from unittest.mock import patch

        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()

        backend = JWTAuthenticationBackend()

        with patch('label_studio_sso.backends.settings') as mock_settings:
            mock_settings.JWT_SSO_VERIFY_NATIVE_TOKEN = False
            mock_settings.JWT_SSO_SECRET = jwt_secret
            mock_settings.JWT_SSO_ALGORITHM = 'HS256'
            mock_settings.JWT_SSO_EMAIL_CLAIM = 'email'
            mock_settings.JWT_SSO_USERNAME_CLAIM = 'username'
            mock_settings.JWT_SSO_AUTO_CREATE_USERS = True
            mock_settings.JWT_SSO_FIRST_NAME_CLAIM = 'first_name'
            mock_settings.JWT_SSO_LAST_NAME_CLAIM = 'last_name'
            user = backend.authenticate(request, token=valid_jwt_token)

        assert user is not None
        assert user.email == user_data['email']

    def test_user_info_update_on_subsequent_login(self, jwt_secret, db):
        """Test user info is updated on subsequent logins"""
        # First login
        payload1 = {
            'email': 'update@example.com',
            'username': 'updateuser',
            'first_name': 'Original',
            'last_name': 'Name',
            'exp': datetime.utcnow() + timedelta(minutes=10)
        }
        token1 = jwt.encode(payload1, jwt_secret, algorithm='HS256')

        from label_studio_sso.backends import JWTAuthenticationBackend

        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()

        backend = JWTAuthenticationBackend()
        user1 = backend.authenticate(request, token=token1)

        assert user1.first_name == 'Original'

        # Second login with updated info
        payload2 = {
            'email': 'update@example.com',
            'username': 'updateuser',
            'first_name': 'Updated',
            'last_name': 'Name',
            'exp': datetime.utcnow() + timedelta(minutes=10)
        }
        token2 = jwt.encode(payload2, jwt_secret, algorithm='HS256')

        user2 = backend.authenticate(request, token=token2)

        assert user2.id == user1.id
        assert user2.first_name == 'Updated'

        # Verify in database
        user_from_db = User.objects.get(email='update@example.com')
        assert user_from_db.first_name == 'Updated'
