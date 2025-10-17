# Changelog

All notable changes to the `label-studio-sso` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [6.0.7] - 2025-10-17

### Fixed

- **Cookie path configuration for reverse proxy scenarios**
  - Changed default `JWT_SSO_COOKIE_PATH` from `/label-studio` to `/`
  - Fixed cookie deletion path in middleware to match cookie setting path
  - Updated all documentation examples to use `path: '/'` instead of `path: '/label-studio'`

### Why This Matters

When Label Studio is accessed through a reverse proxy (e.g., Things Factory at `/label-studio/*`), Label Studio itself runs at the root path `/` internally. The frontend makes API calls to paths like `/api/*`, `/static/*`, etc.

**Problem**: If cookies are set with `path: '/label-studio'`, they won't be sent with Label Studio's internal API requests to `/api/*`, causing authentication failures.

**Solution**: Use `path: '/'` to ensure cookies are sent with all Label Studio requests, regardless of the external proxy path.

This applies to:
- JWT SSO authentication cookies (`ls_auth_token`)
- CSRF protection cookies (`csrftoken`)
- Django session cookies (`sessionid`)

### Configuration Impact

If you're using a reverse proxy setup, update your cookie configuration:

```python
# Label Studio settings.py
JWT_SSO_COOKIE_PATH = '/'  # Changed from '/label-studio'
CSRF_COOKIE_PATH = '/'  # Should be '/', not '/label-studio'
SESSION_COOKIE_PATH = '/'  # Should be '/', not '/label-studio'
```

```javascript
// External application (Node.js/Express)
res.cookie('ls_auth_token', token, {
  path: '/',  // Changed from '/label-studio'
  httpOnly: true,
  secure: true,
  sameSite: 'lax'
})
```

---

## [6.0.3] - 2025-10-16

### Removed

- **Removed authentication.py (JWTSSOSessionAuthentication class)**
  - Class was unnecessary - Token authentication is sufficient for API calls
  - CSRF-exempt session authentication poses security risk
  - Label Studio's `TokenAuthenticationPhaseout` already handles all API authentication
  - No functional impact - v6.0.2 existed for less than 1 hour

### Rationale

The `JWTSSOSessionAuthentication` class added in v6.0.2 was unnecessary because:

1. **Token authentication is sufficient**: Label Studio uses `Authorization: Token` headers for API calls
2. **Security concern**: CSRF exemption creates potential attack vector
3. **Not actually used**: Label Studio frontend doesn't rely on session-only authentication
4. **Middleware handles login**: `JWTAutoLoginMiddleware` already creates Django sessions from JWT

The complete authentication flow works without this class:
```
1. JWT Cookie/URL → JWTAutoLoginMiddleware → Django session created
2. API calls → TokenAuthenticationPhaseout → Authenticated
```

---

## [6.0.2] - 2025-10-16 (DEPRECATED - Use v6.0.3)

### Added

- **DRF Authentication Class for iframe/embedded scenarios**
  - Added `JWTSSOSessionAuthentication` class for REST framework
  - Extends `SessionAuthentication` with CSRF exemption
  - Enables API calls from embedded Label Studio without CSRF tokens
  - Required for Label Studio integration (referenced in REST_FRAMEWORK settings)

### Why This Matters

When Label Studio is embedded in iframe, the frontend needs to make API calls without CSRF tokens. This authentication class allows JWT-authenticated sessions to bypass CSRF checks, enabling seamless API communication in embedded contexts.

---

## [6.0.1] - 2025-10-16

### Documentation

- **Added Label Studio OSS compatibility notice**
  - Added "Label Studio OSS Only" badge to README
  - Added edition compatibility table (OSS vs Enterprise)
  - Clarified that this package is for Label Studio Open Source only
  - Added notice that Enterprise users should use built-in SAML/LDAP/OAuth features
  - Updated package description to include "OSS"
  - Added keywords: "label-studio-oss", "open-source", "oss"
  - Added important notice in CHANGELOG v6.0.0 section

### Changed

- Updated package description from "Native JWT authentication for Label Studio" to "Native JWT authentication for Label Studio OSS"
- Enhanced README Overview section with Edition Compatibility table
- Added "When to Use This Package" guide
- Improved keywords for better discoverability

---

## [6.0.0] - 2025-10-16

### 📌 Important Notice

**This package is for Label Studio OSS (Open Source) only!**

- ✅ **Use this package**: If you're using Label Studio Open Source
- ❌ **Don't use this package**: If you're using Label Studio Enterprise
  - Enterprise has built-in SAML/LDAP/OAuth SSO features
  - See: https://labelstud.io/guide/auth_setup.html

### Breaking Changes

- **REMOVED: Method 1 (External JWT where client generates tokens)**
  - Removed external JWT authentication logic from `backends.py` (~120 lines)
  - Removed all Method 1-specific configuration variables:
    - `JWT_SSO_SECRET` (no longer needed - uses Label Studio's SECRET_KEY)
    - `JWT_SSO_ALGORITHM` (always uses HS256 with SECRET_KEY)
    - `JWT_SSO_EMAIL_CLAIM` (uses user_id instead)
    - `JWT_SSO_USERNAME_CLAIM` (uses user_id instead)
    - `JWT_SSO_FIRST_NAME_CLAIM` (not used in Method 2)
    - `JWT_SSO_LAST_NAME_CLAIM` (not used in Method 2)
    - `JWT_SSO_AUTO_CREATE_USERS` (moved to API-level: `SSO_AUTO_CREATE_USERS`)
    - `JWT_SSO_VERIFY_NATIVE_TOKEN` (no longer needed - always native)
  - Removed Method 1 test cases from test suite (~300 lines)

### Removed

- External JWT generation capability (client-side JWT signing)
- Shared SECRET_KEY requirement between client and Label Studio
- Email/username-based user lookup from JWT claims
- Method 1 documentation from README.md
- Method 1 usage examples (Node.js, Python, Java client-side JWT generation)

### Changed

- **Simplified to single authentication method**: Label Studio Native JWT only
- Backend now always uses Label Studio's `SECRET_KEY` for JWT verification
- JWT tokens always contain `user_id` claim (not email)
- Updated README.md to document only Method 2 (Native JWT)
- Simplified configuration - removed 8 configuration variables
- Updated all tests to use Native JWT authentication
- Updated package description to "Native JWT authentication for Label Studio"

### Migration Guide

If you were using Method 1 (External JWT), migrate to **Method 2 (Native JWT)**:

#### Before (Method 1 - REMOVED)

```python
# Label Studio settings.py
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')  # Shared secret
JWT_SSO_ALGORITHM = 'HS256'
JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_AUTO_CREATE_USERS = True
AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.JWTAuthenticationBackend',
]

# Client generates JWT
token = jwt.sign(
  { email: 'user@example.com', exp: Date.now() + 600 },
  process.env.JWT_SSO_SECRET,  # Shared secret!
  { algorithm: 'HS256' }
);
```

#### After (Method 2 - ONLY OPTION)

```python
# Label Studio settings.py
INSTALLED_APPS += ['rest_framework', 'rest_framework.authtoken']
AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.JWTAuthenticationBackend',
]
JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'
JWT_SSO_COOKIE_NAME = 'ls_auth_token'
SSO_TOKEN_EXPIRY = 600
SSO_AUTO_CREATE_USERS = True

# Add URL patterns
urlpatterns = [
    path('api/sso/', include('label_studio_sso.urls')),
]

# Client requests JWT from Label Studio
const response = await axios.post(
  'http://label-studio:8080/api/sso/token',
  { email: 'user@example.com' },
  { headers: { 'Authorization': `Token ${apiToken}` } }
);
const { token } = response.data;

// Set cookie
res.cookie('ls_auth_token', token, {
  httpOnly: true,
  secure: true
});
```

**Benefits of Method 2**:

- ✅ No shared secrets (more secure)
- ✅ No JWT library needed on client (simpler)
- ✅ Label Studio controls token issuance (centralized)
- ✅ Uses Label Studio's existing SECRET_KEY (no configuration)
- ✅ Admin-level API token required (more secure)

### Reasons for Removal

1. **Security Concerns**: Method 1 required sharing SECRET_KEY with client applications
2. **Implementation Complexity**: Clients had to implement JWT generation
3. **No Real Benefit**: Method 2 provides same functionality with better security
4. **Simpler Architecture**: Single authentication method easier to maintain
5. **Label Studio Controls Tokens**: Centralized token issuance is more secure

### Documentation

- Updated `README.md` to document only Method 2
- Removed all Method 1 examples and configuration
- Simplified troubleshooting guide
- Updated security best practices

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
  path: '/'
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
