"""
Generic JWT Authentication Backend for Label Studio

Authenticates users using JWT tokens from any external system.
Configurable via Django settings for maximum flexibility.
"""

import logging
import requests
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
import jwt
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidSignatureError
)

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthenticationBackend(ModelBackend):
    """
    Generic JWT Authentication Backend for external SSO integration.

    Supports 3 authentication methods:
    1. External JWT (default)
    2. Label Studio Native JWT (JWT_SSO_VERIFY_NATIVE_TOKEN=True)
    3. External Session Cookie (JWT_SSO_SESSION_VERIFY_URL configured)

    Configuration (in Django settings.py):
        # Method 1: External JWT
        JWT_SSO_SECRET: JWT secret key for token verification (required)
        JWT_SSO_ALGORITHM: JWT algorithm (default: 'HS256')
        JWT_SSO_TOKEN_PARAM: URL parameter name for token (default: 'token')
        JWT_SSO_EMAIL_CLAIM: JWT claim containing user email (default: 'email')
        JWT_SSO_USERNAME_CLAIM: JWT claim containing username (optional, defaults to email)
        JWT_SSO_FIRST_NAME_CLAIM: JWT claim for first name (optional, default: 'first_name')
        JWT_SSO_LAST_NAME_CLAIM: JWT claim for last name (optional, default: 'last_name')
        JWT_SSO_AUTO_CREATE_USERS: Auto-create users if not found (default: False)

        # Method 2: Label Studio Native JWT
        JWT_SSO_VERIFY_NATIVE_TOKEN: Enable Label Studio JWT verification (default: False)
        JWT_SSO_NATIVE_USER_ID_CLAIM: Claim containing user ID (default: 'user_id')

        # Method 3: External Session Cookie
        JWT_SSO_SESSION_VERIFY_URL: Client API URL for session verification
        JWT_SSO_SESSION_VERIFY_SECRET: Shared secret for API authentication
        JWT_SSO_SESSION_COOKIE_NAME: Session cookie name (default: 'sessionid')
        JWT_SSO_SESSION_VERIFY_TIMEOUT: API request timeout in seconds (default: 5)
        JWT_SSO_SESSION_CACHE_TTL: Cache TTL for session verification (default: 300)
        JWT_SSO_SESSION_AUTO_CREATE_USERS: Auto-create users from session (default: True)

    Example configuration:
        # Method 1
        JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
        JWT_SSO_ALGORITHM = 'HS256'
        JWT_SSO_TOKEN_PARAM = 'token'
        JWT_SSO_EMAIL_CLAIM = 'email'
        JWT_SSO_AUTO_CREATE_USERS = False

        # Method 2
        JWT_SSO_VERIFY_NATIVE_TOKEN = True
        JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'

        # Method 3
        JWT_SSO_SESSION_VERIFY_URL = 'http://client-api:3000/api/auth/verify-session'
        JWT_SSO_SESSION_VERIFY_SECRET = os.getenv('JWT_SSO_SESSION_VERIFY_SECRET')
        JWT_SSO_SESSION_COOKIE_NAME = 'sessionid'
    """

    def authenticate(self, request, token=None, **kwargs):
        """
        Authenticate user using external JWT token.

        Args:
            request: HttpRequest object
            token: JWT token string from external system

        Returns:
            User object if authentication succeeds, None otherwise
        """
        # Check if this is a DRF Token authentication request - bypass to DRF
        if request:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Token '):
                logger.debug("DRF Token detected, bypassing JWT backend")
                return None

        # Extract token from URL parameter if not provided
        if not token and request:
            token_param = getattr(settings, 'JWT_SSO_TOKEN_PARAM', 'token')
            token = request.GET.get(token_param)

        if not token:
            logger.debug("No JWT token provided")
            return None

        # Get JWT configuration from settings
        verify_native = getattr(settings, 'JWT_SSO_VERIFY_NATIVE_TOKEN', False)
        jwt_algorithm = getattr(settings, 'JWT_SSO_ALGORITHM', 'HS256')
        email_claim = getattr(settings, 'JWT_SSO_EMAIL_CLAIM', 'email')
        username_claim = getattr(settings, 'JWT_SSO_USERNAME_CLAIM', None)
        first_name_claim = getattr(settings, 'JWT_SSO_FIRST_NAME_CLAIM', 'first_name')
        last_name_claim = getattr(settings, 'JWT_SSO_LAST_NAME_CLAIM', 'last_name')
        auto_create = getattr(settings, 'JWT_SSO_AUTO_CREATE_USERS', False)

        try:
            # Method 2: Label Studio Native JWT
            if verify_native:
                logger.info("Verifying Label Studio native JWT token")
                print(f"[JWT Backend] Method 2: Verifying native Label Studio JWT")

                # Use Label Studio's SECRET_KEY for verification
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )

                # Get user by user_id from payload
                user_id_claim = getattr(settings, 'JWT_SSO_NATIVE_USER_ID_CLAIM', 'user_id')
                user_id = payload.get(user_id_claim)

                if not user_id:
                    logger.warning(f"Native JWT token does not contain '{user_id_claim}' claim")
                    return None

                try:
                    user = User.objects.get(pk=user_id)
                    logger.info(f"User authenticated via native JWT: {user.email}")
                    print(f"[JWT Backend] Native JWT auth successful: {user.email}")
                    return user
                except User.DoesNotExist:
                    logger.warning(f"User with ID {user_id} not found")
                    return None

            # Method 1: External JWT
            else:
                logger.info("Verifying external JWT token")
                print(f"[JWT Backend] Method 1: Verifying external JWT")

                jwt_secret = getattr(settings, 'JWT_SSO_SECRET', None)
                if not jwt_secret:
                    logger.error("JWT_SSO_SECRET is not configured")
                    return None

                # Decode and verify JWT token
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=[jwt_algorithm]
                )

            # Extract email from token
            email = payload.get(email_claim)
            username = payload.get(username_claim) if username_claim else None

            print(f"[JWT Backend] Payload: {payload}")
            print(f"[JWT Backend] email_claim={email_claim}, email={email}")
            print(f"[JWT Backend] username_claim={username_claim}, username={username}")

            # If no email, try to find user by username
            if not email:
                if not username:
                    logger.warning(f"JWT token does not contain '{email_claim}' or '{username_claim}' claim")
                    print(f"[JWT Backend] No email or username found in token!")
                    return None

                logger.info(f"No email in JWT, attempting to find user by username: {username}")
                print(f"[JWT Backend] No email in JWT, searching by username: {username}")

                # Try to get existing user by username
                try:
                    user = User.objects.get(username=username)
                    logger.info(f"User found by username: {username}")
                    return user
                except User.DoesNotExist:
                    # Try to find user where email starts with username@
                    try:
                        user = User.objects.get(email__istartswith=f"{username}@")
                        logger.info(f"User found by email prefix: {user.email}")
                        return user
                    except User.DoesNotExist:
                        logger.warning(f"User not found for username: {username}")
                        return None
                    except User.MultipleObjectsReturned:
                        logger.warning(f"Multiple users found with email prefix: {username}@")
                        return None

            logger.info(f"JWT token verified for email: {email}")

            # Get username from token or use email
            if not username:
                username = email

            # Try to get existing user
            try:
                user = User.objects.get(email=email)
                logger.info(f"User found: {email}")

                # Update user info from JWT claims if available
                updated = False
                first_name = payload.get(first_name_claim, '')
                last_name = payload.get(last_name_claim, '')

                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updated = True

                if updated:
                    user.save()
                    logger.info(f"Updated user info for: {email}")

                return user

            except User.DoesNotExist:
                if auto_create:
                    # Auto-create user
                    user = User.objects.create(
                        email=email,
                        username=username,
                        first_name=payload.get(first_name_claim, ''),
                        last_name=payload.get(last_name_claim, '')
                    )
                    logger.info(f"Auto-created user: {email}")
                    return user
                else:
                    logger.warning(f"User not found in Label Studio: {email}")
                    logger.info("Enable JWT_SSO_AUTO_CREATE_USERS or sync users manually")
                    return None

        except ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except InvalidSignatureError:
            logger.error("JWT token signature verification failed")
            return None
        except InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error during JWT authentication: {str(e)}")
            return None

    def get_user(self, user_id):
        """
        Get user by ID (required by Django auth backend interface).
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SessionCookieAuthenticationBackend(ModelBackend):
    """
    Session Cookie Authentication Backend for legacy system integration.

    This backend verifies external session cookies by calling a client API endpoint.

    Configuration (in Django settings.py):
        JWT_SSO_SESSION_VERIFY_URL: Client API URL for session verification (required)
        JWT_SSO_SESSION_VERIFY_SECRET: Shared secret for API authentication (required)
        JWT_SSO_SESSION_COOKIE_NAME: Session cookie name (default: 'sessionid')
        JWT_SSO_SESSION_VERIFY_TIMEOUT: API request timeout in seconds (default: 5)
        JWT_SSO_SESSION_CACHE_TTL: Cache TTL for session verification (default: 300)
        JWT_SSO_SESSION_AUTO_CREATE_USERS: Auto-create users from session (default: True)

    Client API endpoint should:
        - Accept POST request with session cookie
        - Verify session validity
        - Return user information (email, username, first_name, last_name)

    Example API response:
        {
            "valid": true,
            "email": "user@example.com",
            "username": "user",
            "first_name": "John",
            "last_name": "Doe"
        }
    """

    def authenticate(self, request, session_cookie=None, **kwargs):
        """
        Authenticate user by verifying external session cookie with client API.

        Args:
            request: HttpRequest object
            session_cookie: Session cookie value

        Returns:
            User object if authentication succeeds, None otherwise
        """
        # Get configuration
        verify_url = getattr(settings, 'JWT_SSO_SESSION_VERIFY_URL', None)
        verify_secret = getattr(settings, 'JWT_SSO_SESSION_VERIFY_SECRET', None)
        cookie_name = getattr(settings, 'JWT_SSO_SESSION_COOKIE_NAME', 'sessionid')
        timeout = getattr(settings, 'JWT_SSO_SESSION_VERIFY_TIMEOUT', 5)
        cache_ttl = getattr(settings, 'JWT_SSO_SESSION_CACHE_TTL', 300)
        auto_create = getattr(settings, 'JWT_SSO_SESSION_AUTO_CREATE_USERS', True)

        if not verify_url or not verify_secret:
            logger.debug("Session cookie verification not configured")
            return None

        # Extract session cookie from request
        if not session_cookie and request:
            session_cookie = request.COOKIES.get(cookie_name)

        if not session_cookie:
            logger.debug("No session cookie found")
            return None

        logger.info("Attempting session cookie authentication")
        print(f"[Session Backend] Method 3: Verifying external session cookie")

        # Check cache first
        cache_key = f"session_auth:{session_cookie}"
        cached_user_id = cache.get(cache_key)

        if cached_user_id:
            try:
                user = User.objects.get(pk=cached_user_id)
                logger.info(f"Session authentication from cache: {user.email}")
                print(f"[Session Backend] Cache hit: {user.email}")
                return user
            except User.DoesNotExist:
                # Cache is stale, clear it
                cache.delete(cache_key)

        # Call client API to verify session
        try:
            response = requests.post(
                verify_url,
                headers={
                    'Authorization': f'Bearer {verify_secret}',
                    'Content-Type': 'application/json'
                },
                json={'session_cookie': session_cookie},
                timeout=timeout
            )

            if response.status_code != 200:
                logger.warning(f"Session verification failed: HTTP {response.status_code}")
                print(f"[Session Backend] API returned {response.status_code}")
                return None

            data = response.json()

            if not data.get('valid'):
                logger.warning("Session verification failed: invalid session")
                print(f"[Session Backend] Session invalid")
                return None

            # Extract user information
            email = data.get('email')
            username = data.get('username') or email
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')

            if not email:
                logger.warning("Session verification failed: no email in response")
                return None

            logger.info(f"Session verified for email: {email}")
            print(f"[Session Backend] Session verified: {email}")

            # Try to get existing user
            try:
                user = User.objects.get(email=email)
                logger.info(f"User found: {email}")

                # Update user info if provided
                updated = False
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updated = True

                if updated:
                    user.save()
                    logger.info(f"Updated user info for: {email}")

                # Cache the result
                cache.set(cache_key, user.id, cache_ttl)

                return user

            except User.DoesNotExist:
                if auto_create:
                    # Auto-create user
                    user = User.objects.create(
                        email=email,
                        username=username,
                        first_name=first_name,
                        last_name=last_name
                    )
                    logger.info(f"Auto-created user: {email}")
                    print(f"[Session Backend] Auto-created user: {email}")

                    # Cache the result
                    cache.set(cache_key, user.id, cache_ttl)

                    return user
                else:
                    logger.warning(f"User not found in Label Studio: {email}")
                    logger.info("Enable JWT_SSO_SESSION_AUTO_CREATE_USERS or sync users manually")
                    return None

        except requests.RequestException as e:
            logger.error(f"Session verification request failed: {str(e)}")
            print(f"[Session Backend] API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error during session authentication: {str(e)}")
            return None

    def get_user(self, user_id):
        """
        Get user by ID (required by Django auth backend interface).
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
