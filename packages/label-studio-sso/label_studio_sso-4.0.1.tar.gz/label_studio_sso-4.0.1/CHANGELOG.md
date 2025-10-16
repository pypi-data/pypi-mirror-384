# Changelog

All notable changes to the `label-studio-sso` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
