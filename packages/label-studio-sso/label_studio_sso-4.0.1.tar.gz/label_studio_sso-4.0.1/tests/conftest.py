"""
Pytest configuration for label-studio-sso tests
"""

import pytest
import jwt
from datetime import datetime, timedelta
from django.conf import settings


@pytest.fixture
def jwt_secret():
    """JWT secret key for tests"""
    return settings.JWT_SSO_SECRET


@pytest.fixture
def user_data():
    """Sample user data for tests"""
    return {
        'email': 'test@example.com',
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def valid_jwt_token(jwt_secret, user_data):
    """Generate a valid JWT token for tests"""
    payload = {
        **user_data,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=10)
    }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')
