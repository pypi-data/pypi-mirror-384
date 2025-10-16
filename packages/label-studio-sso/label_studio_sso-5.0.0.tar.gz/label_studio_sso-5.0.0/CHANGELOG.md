# Changelog

All notable changes to the `label-studio-sso` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [5.0.0] - 2025-10-16

### Breaking Changes

- **REMOVED: Method 3 (External Session Cookie Authentication)**
  - Removed `SessionCookieAuthenticationBackend` class from `backends.py` (~170 lines)
  - Removed session cookie verification logic from `middleware.py`
  - Removed session-related configuration variables:
    - `JWT_SSO_SESSION_VERIFY_URL`
    - `JWT_SSO_SESSION_VERIFY_SECRET`
    - `JWT_SSO_SESSION_COOKIE_NAME`
    - `JWT_SSO_SESSION_VERIFY_TIMEOUT`
    - `JWT_SSO_SESSION_CACHE_TTL`
    - `JWT_SSO_SESSION_AUTO_CREATE_USERS`
  - Removed session authentication tests from test suite

### Removed

- `SessionCookieAuthenticationBackend` class
- `IMPLEMENTATION_GUIDE.md` (primarily focused on Method 3)
- `CONFIGURATION.md` (contained extensive Method 3 examples)
- All session verification API integration code
- Circular dependency with external client systems

### Changed

- Updated documentation to reflect 2 authentication methods (previously 3)
- Simplified middleware to support only JWT-based authentication
- Updated `JWTAuthenticationBackend` docstring (removed Method 3 references)
- Cleaned up test files (removed ~350 lines of Method 3 tests)

### Migration Guide

If you were using Method 3, migrate to **Method 2 (Native JWT)** - the recommended approach:

#### Before (Method 3)
```python
# Label Studio settings.py
JWT_SSO_SESSION_VERIFY_URL = 'http://client:3000/api/auth/verify-session'
JWT_SSO_SESSION_VERIFY_SECRET = 'shared-secret'
AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.SessionCookieAuthenticationBackend',
]

# Client API
@app.post('/api/auth/verify-session')
def verify_session(request):
    # Session verification logic...
    return {"valid": True, "email": "user@example.com"}
```

#### After (Method 2 - Recommended)
```python
# Label Studio settings.py
INSTALLED_APPS += ['rest_framework', 'rest_framework.authtoken']
AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.JWTAuthenticationBackend',
]
JWT_SSO_VERIFY_NATIVE_TOKEN = True

# Client - Call Label Studio API
response = await axios.post(
  'http://label-studio:8080/api/sso/token',
  { email: 'user@example.com' },
  { headers: { 'Authorization': `Token ${apiToken}` } }
)
const { token } = response.data

// Set cookie
ctx.cookies.set('ls_auth_token', token, {
  httpOnly: true,
  secure: true,
  path: '/label-studio'
})
```

**Benefits of Method 2**:
- ✅ No client API required (remove session verification endpoint)
- ✅ Reduced network calls (1 call instead of per-request verification)
- ✅ No circular dependency
- ✅ Simpler implementation

### Reasons for Removal

1. **Circular Dependency**: Method 3 created a circular dependency between Label Studio and client systems
2. **Performance Issues**: Every request required an external API call for session verification
3. **No Real-World Usage**: No production systems were using Method 3
4. **Method 2 Superior**: Method 2 (Native JWT) provides the same functionality with better performance and simpler architecture

### Documentation

- Added `METHOD3_REMOVAL_REPORT.md` with detailed removal rationale
- Updated `README.md` to reflect 2 authentication methods
- Simplified all configuration examples

---

## [4.0.1] - 2025-10-15

### Fixed

- Fixed SSO token issuance API authentication
- Changed from `ssoApiSecret` (request body) to `apiToken` (Authorization header)
- Standardized authentication pattern across all API calls

### Security

- Added admin/staff privilege check for SSO token issuance
- Ensured consistent use of DRF Token authentication

### Documentation

- Updated `INTEGRATION.md` with correct authentication flow
- Added comprehensive code review in `REVIEW_SUMMARY.md`
- Clarified `apiToken` usage in config files

---

## [4.0.0] - 2025-10-14

### Added

- Support for 3 authentication methods:
  1. External JWT (default)
  2. Label Studio Native JWT
  3. External Session Cookie (later removed in v5.0.0)

### Features

- JWT cookie-based authentication (HttpOnly, Secure)
- Session-based authentication with external API verification
- Caching for session verification (5 min TTL)
- Auto-user creation support
- Configurable JWT claims mapping

---

## [1.0.0] - 2025-10-02

### Added

- **Generic JWT Authentication Backend** (`JWTAuthenticationBackend`)

  - Configurable JWT secret, algorithm, and token parameter
  - Customizable JWT claim mapping (email, username, first_name, last_name)
  - Auto-create users option
  - User info auto-update from JWT claims

- **Auto-Login Middleware** (`JWTAutoLoginMiddleware`)

  - Automatic user authentication from URL token parameter
  - Configurable token parameter name
  - Session management

- **Backward Compatibility**

  - `ClientApplicationJWTBackend` alias for Client Application integration
  - `ClientApplicationAutoLoginMiddleware` alias

- **Configuration Options**

  - `JWT_SSO_SECRET` - JWT secret key (required)
  - `JWT_SSO_ALGORITHM` - JWT algorithm (default: HS256)
  - `JWT_SSO_TOKEN_PARAM` - URL token parameter (default: token)
  - `JWT_SSO_EMAIL_CLAIM` - Email claim name (default: email)
  - `JWT_SSO_USERNAME_CLAIM` - Username claim name (optional)
  - `JWT_SSO_FIRST_NAME_CLAIM` - First name claim (default: first_name)
  - `JWT_SSO_LAST_NAME_CLAIM` - Last name claim (default: last_name)
  - `JWT_SSO_AUTO_CREATE_USERS` - Auto-create users (default: False)

- **Documentation**

  - README.md - Package overview and quick start
  - CONFIGURATION.md - Detailed configuration guide with examples
  - LICENSE - MIT License

- **Tests**
  - Unit tests for JWT authentication backend
  - Unit tests for auto-login middleware
  - Test configuration with pytest

### Features

- ✅ Works with any JWT-based system
- ✅ Minimal Label Studio code modification
- ✅ Independent pip package
- ✅ Comprehensive logging
- ✅ Security best practices

### Supported Systems

- Client Application (original use case)
- Auth0, Keycloak, Okta
- Custom Node.js/Django/Flask/Spring Boot applications
- Any system that can issue JWT tokens

---

## [0.1.0] - 2025-10-01 (Initial Design)

### Planned

- Client Application specific JWT authentication
- Initial proof of concept

### Changed

- **2025-10-02**: Generalized from Client Application specific to generic JWT SSO
  - Renamed classes: `ClientApplicationJWTBackend` → `JWTAuthenticationBackend`
  - Added configurable JWT claim mapping
  - Added auto-create users feature
  - Made backward compatible with Client Application

---

## Future Releases

### [1.1.0] - Planned

- Support for RS256/RS512 algorithms (public/private key)
- JWT token caching for performance
- Custom user creation callback
- More granular permission mapping

### [1.2.0] - Planned

- Multi-tenant support
- Token refresh mechanism
- Admin UI for configuration
- Metrics and monitoring hooks

### [2.0.0] - Planned (Breaking Changes)

- Django 5.0 support
- Python 3.12+ only
- Async middleware support
- GraphQL authentication support

---

## Migration Guides

### From Client Application Custom Implementation

If you have a custom Client Application JWT authentication:

```python
# Old (custom implementation)
AUTHENTICATION_BACKENDS = [
    'your_app.backends.ClientApplicationAuthenticationBackend',
]

# New (label-studio-sso package)
AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.JWTAuthenticationBackend',
]

# Or use backward compatible alias
AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.ClientApplicationJWTBackend',
]
```

---

## Support

- **Issues**: [GitHub Issues](https://github.com/aidoop/label-studio-sso/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aidoop/label-studio-sso/discussions)
- **Documentation**: [README](./README.md) | [CONFIGURATION](./CONFIGURATION.md)
