# Label Studio SSO - Universal Authentication Plugin

Universal authentication plugin for Label Studio supporting multiple SSO methods.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django: 4.2+](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Version: 3.0.0](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/aidoop/label-studio-sso)
[![Tests](https://github.com/aidoop/label-studio-sso/actions/workflows/test.yml/badge.svg)](https://github.com/aidoop/label-studio-sso/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/aidoop/label-studio-sso)

---

## 🎯 Overview

This package provides flexible authentication backends for **Label Studio** that support multiple SSO integration methods.

> **📌 About "SSO"**: This package provides **authentication integration** between external systems and Label Studio, commonly referred to as "SSO integration" in the industry. While not traditional Single Sign-On (one login → all services), it enables seamless authentication where users don't need to login separately to Label Studio. See [Understanding SSO](#-understanding-sso) for details.

### 2 Authentication Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **Method 1: External JWT** | Client generates JWT with shared secret | Independent systems, Auth0, Keycloak |
| **Method 2: Native JWT (Recommended)** | Label Studio issues JWT tokens via API | All integrations, simplest and most secure |

### Key Features

- ✅ **Two Authentication Methods**: External JWT, Native JWT (recommended)
- ✅ **Multiple Token Transmission**: Cookie (recommended), URL parameter
- ✅ **Automatic Fallback**: Django Session → JWT Cookie → JWT URL
- ✅ **Secure Cookie-based Auth**: HttpOnly cookies, no URL exposure
- ✅ **Expired Token Cleanup**: Automatic deletion of expired JWT cookies
- ✅ **Configurable Claims**: Map any JWT claim to user fields
- ✅ **Auto-User Creation**: Optionally create users from JWT data
- ✅ **Zero Label Studio Modifications**: Pure Django plugin
- ✅ **Framework Agnostic**: Works with Node.js, Python, Java, .NET, etc.

---

## 📦 Installation

### 1. Install via pip

```bash
pip install label-studio-sso
```

---

## 🚀 Quick Start

Choose the authentication method that best fits your use case:

### Method 1: External JWT (Recommended)

**Use when**: You have an independent authentication system (Node.js, Python, Auth0, Keycloak, etc.)

**1. Configure Label Studio**:

```python
# label_studio/core/settings/label_studio.py

INSTALLED_APPS += ['label_studio_sso']

AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.JWTAuthenticationBackend',  # Add first
    # ... other backends ...
]

MIDDLEWARE += ['label_studio_sso.middleware.JWTAutoLoginMiddleware']

# Method 1 Configuration
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')  # Shared with client
JWT_SSO_ALGORITHM = 'HS256'

# 🔐 Cookie-based (Recommended - More Secure)
JWT_SSO_COOKIE_NAME = 'ls_auth_token'  # HttpOnly cookie
JWT_SSO_COOKIE_PATH = '/label-studio'  # Optional, default path

# 🔓 URL-based (Legacy - Less Secure)
JWT_SSO_TOKEN_PARAM = 'token'  # URL parameter (for backward compatibility)

JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_AUTO_CREATE_USERS = False  # or True
```

**2. Generate JWT in your client**:

```javascript
// Node.js example
const jwt = require('jsonwebtoken');

const token = jwt.sign(
  { email: 'user@example.com', exp: Math.floor(Date.now() / 1000) + 600 },
  process.env.JWT_SSO_SECRET,
  { algorithm: 'HS256' }
);

// ✅ Recommended: Set HttpOnly cookie (more secure)
response.cookie('ls_auth_token', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  path: '/label-studio',
  maxAge: 600000  // 10 minutes
});

// Then open Label Studio (no token in URL!)
const iframe = document.createElement('iframe');
iframe.src = 'http://labelstudio.example.com/';  // Clean URL!

// ⚠️ Legacy: URL parameter (less secure, backward compatibility)
// iframe.src = `http://labelstudio.example.com?token=${token}`;
```

---

### Method 2: Label Studio Issues JWT (Recommended for iframe integration)

**Use when**: You want Label Studio to issue its own JWT tokens - most secure for same-origin setups

**1. Configure Label Studio**:

```python
# label_studio/core/settings/label_studio.py

INSTALLED_APPS += ['label_studio_sso']
AUTHENTICATION_BACKENDS = ['label_studio_sso.backends.JWTAuthenticationBackend', ...]
MIDDLEWARE += ['label_studio_sso.middleware.JWTAutoLoginMiddleware']

# Add URL patterns
from django.urls import path, include
urlpatterns += [
    path('', include('label_studio_sso.urls')),
]

# Method 2 Configuration
JWT_SSO_VERIFY_NATIVE_TOKEN = True  # Use Label Studio's own SECRET_KEY
JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'
JWT_SSO_COOKIE_NAME = 'ls_auth_token'  # Cookie-based (recommended)

# API Configuration (Method 2)
SSO_TOKEN_EXPIRY = 600  # 10 minutes
SSO_AUTO_CREATE_USERS = True  # Auto-create users

# Django REST Framework (required for Token authentication)
INSTALLED_APPS += ['rest_framework', 'rest_framework.authtoken']
```

**2. Client requests JWT from Label Studio API**:

```javascript
// Node.js/Express example
const axios = require('axios');

// Step 1: Get Label Studio admin API token
// (from Label Studio: Account Settings → Access Token)
const labelStudioApiToken = process.env.LABEL_STUDIO_API_TOKEN;

// Step 2: Request JWT token from Label Studio
const response = await axios.post(
  'http://labelstudio.example.com/api/sso/token',
  { email: user.email },
  {
    headers: {
      'Authorization': `Token ${labelStudioApiToken}`,
      'Content-Type': 'application/json'
    }
  }
);

const { token, expires_in } = response.data;

// Step 3: Set HttpOnly cookie (recommended)
res.cookie('ls_auth_token', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  path: '/label-studio',
  maxAge: expires_in * 1000
});

// Step 4: Open Label Studio iframe (clean URL!)
const iframe = document.createElement('iframe');
iframe.src = 'http://labelstudio.example.com/';

// ⚠️ Or URL parameter (legacy)
// iframe.src = `http://labelstudio.example.com?token=${token}`;
```

**Advantages**:
- ✅ Uses Label Studio's existing API token system
- ✅ No additional secrets needed
- ✅ Admin-level authentication required
- ✅ Label Studio controls token issuance
- ✅ Secure HttpOnly cookies
- ✅ Clean URLs

---

### How It Works

```
External System (Your App)
  ↓ Generate JWT token with user info
  ↓ Create URL: https://label-studio.example.com?token=eyJhbGc...
  ↓
User clicks link or iframe loads
  ↓
Label Studio
  ↓ JWTAutoLoginMiddleware extracts token from URL
  ↓ JWTAuthenticationBackend validates JWT signature
  ↓ Extract user info from JWT claims
  ↓ Find or create Label Studio user
  ↓ Auto-login user
  ✅ User authenticated!
```

---

## 🔧 Usage Examples

### Example 1: Node.js/Express Integration

```javascript
const jwt = require('jsonwebtoken');

// Generate JWT token for user
const token = jwt.sign(
  {
    email: "user@example.com",
    username: "john_doe",
    first_name: "John",
    last_name: "Doe",
    exp: Math.floor(Date.now() / 1000) + (10 * 60)  // 10 minutes
  },
  process.env.JWT_SSO_SECRET,
  { algorithm: 'HS256' }
);

// Redirect user to Label Studio
const labelStudioUrl = `https://label-studio.example.com?token=${token}`;
res.redirect(labelStudioUrl);
```

### Example 2: Python/Django Integration

```python
import jwt
from datetime import datetime, timedelta

# Generate JWT token
token = jwt.encode(
    {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'exp': datetime.utcnow() + timedelta(minutes=10)
    },
    settings.JWT_SSO_SECRET,
    algorithm='HS256'
)

# Embed in iframe or redirect
label_studio_url = f"https://label-studio.example.com?token={token}"
```

### Example 3: Java/Spring Boot Integration

```java
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;

// Generate JWT token
String token = Jwts.builder()
    .claim("email", user.getEmail())
    .claim("first_name", user.getFirstName())
    .claim("last_name", user.getLastName())
    .setExpiration(new Date(System.currentTimeMillis() + 600000))  // 10 minutes
    .signWith(SignatureAlgorithm.HS256, jwtSecret)
    .compact();

// Redirect to Label Studio
String labelStudioUrl = "https://label-studio.example.com?token=" + token;
return "redirect:" + labelStudioUrl;
```

### Example 4: Cookie-Based Authentication (Reverse Proxy)

For reverse proxy scenarios where Label Studio is behind the same domain:

**Backend (Node.js/Koa):**
```javascript
const jwt = require('jsonwebtoken');

app.use('/label-studio', async (ctx, next) => {
  const user = ctx.state.user; // Already authenticated user

  if (user && !ctx.cookies.get('jwt_auth_token')) {
    // Generate JWT token
    const token = jwt.sign(
      {
        email: user.email,
        username: user.username,
        exp: Math.floor(Date.now() / 1000) + (10 * 60)
      },
      process.env.JWT_SSO_SECRET,
      { algorithm: 'HS256' }
    );

    // Set JWT cookie
    ctx.cookies.set('jwt_auth_token', token, {
      path: '/label-studio',
      httpOnly: true,
      secure: true,
      sameSite: 'Lax'
    });
  }

  // Proxy to Label Studio
  await proxyToLabelStudio(ctx);
});
```

**Label Studio Settings:**
```python
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
JWT_SSO_COOKIE_NAME = 'jwt_auth_token'  # Enable cookie-based auth
JWT_SSO_EMAIL_CLAIM = 'email'
```

**Benefits:**
- ✅ No JWT token in URL (more secure)
- ✅ Seamless iframe integration
- ✅ Automatic session renewal
- ✅ Same-origin cookie sharing

### Example 5: Hybrid Approach (URL + Cookie)

Best of both worlds - initial login via URL, subsequent access via cookie:

**Label Studio Settings:**
```python
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
JWT_SSO_TOKEN_PARAM = 'token'           # URL parameter auth
JWT_SSO_COOKIE_NAME = 'jwt_auth_token'  # Cookie auth (fallback)
JWT_SSO_EMAIL_CLAIM = 'email'
```

**Flow:**
1. User clicks email link: `https://ls.example.com?token=eyJhbGc...`
2. JWTAutoLoginMiddleware extracts token from URL
3. User authenticated, Django session created
4. Cookie `jwt_auth_token` set for future requests
5. Subsequent requests use cookie (no token in URL needed)

### Example 6: Custom JWT Claims Mapping

If your JWT uses different claim names:

```bash
# Configure custom JWT claim mapping
export JWT_SSO_EMAIL_CLAIM="user_email"
export JWT_SSO_USERNAME_CLAIM="username"
export JWT_SSO_FIRST_NAME_CLAIM="given_name"
export JWT_SSO_LAST_NAME_CLAIM="family_name"
```

Then your JWT payload:
```json
{
  "user_email": "user@example.com",
  "username": "john_doe",
  "given_name": "John",
  "family_name": "Doe",
  "exp": 1234567890
}
```

---

## ⚙️ Configuration Options

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `JWT_SSO_SECRET` | Shared secret key for JWT verification | `"your-secret-key"` |

### Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `JWT_SSO_ALGORITHM` | `HS256` | JWT algorithm (HS256, HS512, RS256, etc.) |
| `JWT_SSO_TOKEN_PARAM` | `token` | URL parameter name for JWT token |
| `JWT_SSO_COOKIE_NAME` | `None` | Cookie name for JWT token (optional, for reverse proxy) |
| `JWT_SSO_EMAIL_CLAIM` | `email` | JWT claim containing user email |
| `JWT_SSO_USERNAME_CLAIM` | `None` | JWT claim containing username (optional) |
| `JWT_SSO_FIRST_NAME_CLAIM` | `first_name` | JWT claim for first name |
| `JWT_SSO_LAST_NAME_CLAIM` | `last_name` | JWT claim for last name |
| `JWT_SSO_AUTO_CREATE_USERS` | `false` | Auto-create users if not found in Label Studio |

---

## 🔒 Security Best Practices

### 1. Use Strong Secrets

Generate a cryptographically secure secret:

```python
import secrets
secret = secrets.token_urlsafe(32)
print(f"JWT_SSO_SECRET={secret}")
```

### 2. Use HTTPS Only

JWT tokens in URLs are visible in browser history and server logs. **Always use HTTPS** in production.

### 3. Short Token Expiration

Use short-lived tokens (5-10 minutes recommended):

```javascript
// Good: 10 minutes
exp: Math.floor(Date.now() / 1000) + (10 * 60)

// Bad: 24 hours
exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60)
```

### 4. Never Hardcode Secrets

Always use environment variables:

```bash
# Good
export JWT_SSO_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Bad
JWT_SSO_SECRET = "hardcoded-secret"  # ❌ Never do this
```

---

## 🧪 Testing

### Local Testing

```bash
# 1. Set environment variables
export JWT_SSO_SECRET="test-secret-key"
export JWT_SSO_AUTO_CREATE_USERS="true"

# 2. Start Label Studio
cd /path/to/label-studio
python manage.py runserver

# 3. Generate test token
python -c "
import jwt
from datetime import datetime, timedelta

token = jwt.encode(
    {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'exp': datetime.utcnow() + timedelta(minutes=10)
    },
    'test-secret-key',
    algorithm='HS256'
)
print(f'http://localhost:8080?token={token}')
"

# 4. Open the URL in browser
```

---

## 📋 Requirements

- **Python**: 3.8+
- **Label Studio**: 1.7.0+
- **Django**: 3.2+
- **PyJWT**: 2.0+

---

## 🛠️ Development

### Install from Source

```bash
git clone https://github.com/aidoop/label-studio-sso.git
cd label-studio-sso
pip install -e .
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=label_studio_sso --cov-report=term-missing

# Run specific test file
pytest tests/test_backends.py -v
```

### Code Quality

```bash
# Format code with black
black label_studio_sso tests

# Sort imports
isort label_studio_sso tests

# Lint with flake8
flake8 label_studio_sso tests
```

### Continuous Integration

This project uses GitHub Actions for CI/CD:

- **Tests Workflow** (`.github/workflows/test.yml`): Runs on every push and PR
  - Tests across Python 3.8-3.12 and Django 4.2-5.1
  - 100% code coverage requirement
  - Linting and code formatting checks

- **Publish Workflow** (`.github/workflows/publish.yml`): Runs on release
  - Automated testing before deployment
  - Builds and publishes to PyPI

### Build Package

```bash
python -m build
```

---

## 🤝 Contributing

Issues and pull requests are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🔗 Related Projects

- [Label Studio](https://github.com/HumanSignal/label-studio) - Open source data labeling platform
- [PyJWT](https://github.com/jpadilla/pyjwt) - JSON Web Token implementation in Python

---

## 💡 Use Cases

This package can integrate Label Studio with:

- ✅ Custom web portals (Node.js, Django, Flask, Spring Boot, .NET Core)
- ✅ Enterprise SSO systems (Keycloak, Auth0, Okta with JWT)
- ✅ Internal authentication services
- ✅ Microservices architectures
- ✅ Any system that can generate JWT tokens

---

## 📞 Support

For issues, questions, or feature requests, please open an issue on [GitHub](https://github.com/aidoop/label-studio-sso/issues).

---

## 🚀 Changelog

### v5.0.0 (2025-10-16) - Breaking Changes
- ❌ **REMOVED**: Method 3 (External Session Cookie Authentication)
  - Removed `SessionCookieAuthenticationBackend` class
  - Removed session verification logic from middleware
  - Removed session-related configuration variables
- ✅ **Simplified**: Now supports 2 authentication methods only
  - Method 1: External JWT (client generates)
  - Method 2: Native JWT (Label Studio issues) - **Recommended**
- 📝 Documentation cleanup and clarification
- 🎯 Focused on proven, efficient authentication patterns

### v4.0.1 (2025-01-XX)
- ✨ Added Label Studio Native JWT token issuance API
- ✨ Added apiToken-based authentication for SSO token API
- 🔒 Enhanced security with admin-level token verification
- 📝 Complete documentation overhaul

### v3.0.0
- ✨ Added 3 authentication methods (later reduced to 2)
- ✨ Added JWT cookie support
- 🔒 Enhanced security with HttpOnly cookies

### v2.0.x
- Session-based authentication (deprecated)

### v1.0.x
- Initial JWT URL parameter support

---

## 📖 Understanding SSO

### What is "SSO" in this context?

The term "SSO" (Single Sign-On) in this package refers to **authentication integration** rather than traditional Single Sign-On.

### Traditional SSO vs This Package

| Feature | Traditional SSO | label-studio-sso |
|---------|----------------|------------------|
| **Definition** | One login across multiple services | External system → Label Studio auth bridge |
| **Example** | Google login → Gmail, YouTube, Drive all accessible | Your app login → Label Studio accessible via JWT |
| **Session Sharing** | ✅ Automatic across all services | ❌ Each system has own session |
| **User Experience** | Login once, access everywhere | Login to your app, auto-login to Label Studio |
| **Implementation** | Complex (SAML, OAuth, OpenID) | Simple (JWT tokens) |
| **Best For** | Enterprise-wide authentication | Embedding Label Studio in your app |

### Why We Call It "SSO"

1. **Industry Convention**: JWT-based authentication bridges are commonly called "SSO integrations"
   - Examples: `django-google-sso`, `django-microsoft-sso`, `djangorestframework-sso`
   - All use token-based auth but are labeled "SSO"

2. **User Perspective**: Users experience seamless authentication
   - Login to your application → Label Studio automatically authenticates
   - No separate login required for Label Studio
   - This **feels like SSO** to end users

3. **Label Studio Ecosystem**: Label Studio Enterprise uses "SSO" for SAML authentication
   - Our package follows the same terminology
   - Easier for Label Studio users to discover and understand

### What This Package Actually Does

```
┌─────────────────────────────────────────────────────────────┐
│ Your Application (Node.js, Django, Java, etc.)             │
│  ↓ User logs in                                             │
│  ↓ Application generates JWT token (or uses existing session)│
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ JWT Token or Session Cookie
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ label-studio-sso (This Package)                             │
│  ↓ Verifies JWT signature / Validates session               │
│  ↓ Extracts user information                                │
│  ↓ Creates Django session                                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Authenticated Session
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Label Studio                                                │
│  ✅ User authenticated without separate login               │
│  ✅ Can use all Label Studio features                       │
└─────────────────────────────────────────────────────────────┘
```

### More Accurate Terms

If we were to use technically precise terminology, this package could be called:
- `label-studio-auth-bridge` - Authentication bridge
- `label-studio-jwt-auth` - JWT-based authentication
- `label-studio-external-auth` - External authentication integration

However, **"SSO"** is:
- ✅ More recognizable to users
- ✅ Consistent with industry practice
- ✅ Aligned with Label Studio's own terminology
- ✅ Better for discoverability (search engines, PyPI)

### When You Need True SSO

If you need traditional Single Sign-On (one login → all services), consider:
- **Label Studio Enterprise**: Built-in SAML SSO with Okta, Google, Azure AD
- **OAuth/OIDC**: Use `django-allauth` or similar packages
- **SAML**: Use `django-saml2-auth` for SAML-based SSO
- **CAS**: Use `django-mama-cas` for CAS protocol

This package is specifically designed for **iframe/popup integration** where:
1. You have an existing application with authentication
2. You want to embed Label Studio seamlessly
3. Users should not login separately to Label Studio
4. JWT tokens or session cookies are acceptable

---

## 🎯 Summary

**label-studio-sso** = Authentication integration package
**Not** = Traditional enterprise SSO system
**Best for** = Embedding Label Studio in your application
**Works with** = Any system that can generate JWT tokens or verify sessions

The name reflects common usage in the Django/Label Studio community rather than strict technical classification.
