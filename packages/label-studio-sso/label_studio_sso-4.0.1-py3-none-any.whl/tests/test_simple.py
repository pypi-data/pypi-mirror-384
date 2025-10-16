"""
Simple unit tests for JWT SSO
"""
import pytest
import jwt
from datetime import datetime, timedelta
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings

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
        """Test authentication with valid token"""
        backend = JWTAuthenticationBackend()
        
        # Create user
        user = User.objects.create(
            email='test@example.com',
            username='testuser'
        )
        
        # Create token
        token = jwt.encode(
            {
                'email': 'test@example.com',
                'username': 'testuser',
                'exp': datetime.utcnow() + timedelta(minutes=10)
            },
            settings.JWT_SSO_SECRET,
            algorithm='HS256'
        )
        
        # Create request
        factory = RequestFactory()
        request = factory.get('/')
        
        # Authenticate
        authenticated_user = backend.authenticate(request, token=token)
        
        assert authenticated_user is not None
        assert authenticated_user.email == 'test@example.com'
    
    def test_authenticate_with_invalid_token(self):
        """Test authentication with invalid token"""
        backend = JWTAuthenticationBackend()
        
        factory = RequestFactory()
        request = factory.get('/')
        
        # Authenticate with invalid token
        authenticated_user = backend.authenticate(request, token='invalid-token')
        
        assert authenticated_user is None


@pytest.mark.django_db
class TestJWTMiddleware:
    def test_import(self):
        """Test that middleware can be imported"""
        def get_response(request):
            return None
        
        middleware = JWTAutoLoginMiddleware(get_response)
        assert middleware is not None
