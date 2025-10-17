# Label Studio SSO - Native JWT Authentication

Native JWT authentication plugin for Label Studio enabling seamless SSO integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django: 4.2+](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Version: 6.0.7](https://img.shields.io/badge/version-6.0.7-blue.svg)](https://github.com/aidoop/label-studio-sso)
[![Tests](https://github.com/aidoop/label-studio-sso/actions/workflows/test.yml/badge.svg)](https://github.com/aidoop/label-studio-sso/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/aidoop/label-studio-sso)
[![Label Studio: OSS Only](https://img.shields.io/badge/Label%20Studio-OSS%20Only-orange.svg)](https://github.com/HumanSignal/label-studio)

> **⚠️ Breaking Changes in v6.0.0**: Method 1 (External JWT) has been removed. See [Migration Guide](./MIGRATION_GUIDE_v6.md) for upgrade instructions.

> **📌 For Label Studio OSS Only**: This package is designed for **Label Studio Open Source** edition. If you're using **Label Studio Enterprise**, use the built-in SAML/LDAP/OAuth SSO features instead.

---

## 🎯 Overview

This package provides JWT-based authentication integration for **Label Studio Open Source (OSS)**, enabling seamless SSO from external applications.

### 📊 Label Studio Edition Compatibility

| Edition | SSO Support | Use This Package? |
|---------|-------------|-------------------|
| **Label Studio OSS** | ❌ No built-in SSO | ✅ **YES** - Use this package |
| **Label Studio Enterprise** | ✅ Built-in SAML/LDAP/OAuth | ❌ **NO** - Use built-in features |

### When to Use This Package

**✅ Use label-studio-sso if:**
- You're using Label Studio **Open Source** (free version)
- You want to embed Label Studio in your application
- You need JWT-based authentication integration
- You want users to auto-login without separate credentials

**❌ Don't use this package if:**
- You're using **Label Studio Enterprise** (commercial version)
  - Enterprise has built-in SAML, LDAP, and OAuth SSO
  - Use those instead: [Label Studio Enterprise SSO Docs](https://labelstud.io/guide/auth_setup.html)
- You need traditional Single Sign-On across multiple services
  - Consider SAML, OAuth, or OpenID Connect instead

> **📌 About "SSO"**: This package provides **authentication integration** between external systems and Label Studio, commonly referred to as "SSO integration" in the industry. While not traditional Single Sign-On (one login → all services), it enables seamless authentication where users don't need to login separately to Label Studio. See [Understanding SSO](#-understanding-sso) for details.

### How It Works

Label Studio issues JWT tokens via a secure API endpoint. Your client application requests tokens and uses them to authenticate users automatically.

### Key Features

- ✅ **Simple Architecture**: Label Studio issues JWT tokens, no shared secrets needed
- ✅ **Multiple Token Transmission**: Cookie (recommended), URL parameter
- ✅ **Automatic Fallback**: Django Session → JWT Cookie → JWT URL
- ✅ **Secure Cookie-based Auth**: HttpOnly cookies, no URL exposure
- ✅ **Expired Token Cleanup**: Automatic deletion of expired JWT cookies
- ✅ **Auto-User Creation**: Optionally create users via API
- ✅ **Zero Label Studio Code Modifications**: Pure Django plugin
- ✅ **Framework Agnostic**: Works with Node.js, Python, Java, .NET, etc.

---

## 📦 Installation

### 1. Install the package

```bash
pip install label-studio-sso
```

### 2. Configure Label Studio

#### Option A: Source Installation (Recommended for Development)

If you installed Label Studio from source:

```bash
# 1. Find your Label Studio installation
cd /path/to/label-studio

# 2. Install label-studio-sso in the same environment
pip install label-studio-sso

# 3. Edit settings file
# File: label_studio/core/settings/label_studio.py
```

#### Option B: Docker Installation

If you're using Label Studio Docker:

```bash
# 1. Create a custom Dockerfile
FROM heartexlabs/label-studio:latest

# Install label-studio-sso
RUN pip install label-studio-sso

# 2. Create custom settings file
# Mount settings at runtime or build into image
```

#### Option C: Pip Installation

If you installed Label Studio via pip:

```bash
# 1. Find Label Studio settings location
python -c "import label_studio; print(label_studio.__file__)"
# Output example: /usr/local/lib/python3.9/site-packages/label_studio/__init__.py

# 2. Navigate to settings directory
cd /usr/local/lib/python3.9/site-packages/label_studio/core/settings/

# 3. Edit label_studio.py
```

---

## 🚀 Quick Start

### Step 1: Edit Label Studio Settings

Edit `label_studio/core/settings/label_studio.py`:

```python
# File: label_studio/core/settings/label_studio.py
import os

# Add to INSTALLED_APPS
INSTALLED_APPS += [
    'label_studio_sso',
    'rest_framework',  # Required for API
    'rest_framework.authtoken',  # Required for Token authentication
]

# Add to AUTHENTICATION_BACKENDS (must be BEFORE existing backends)
AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.JWTAuthenticationBackend',  # Add this FIRST
    'django.contrib.auth.backends.ModelBackend',
    # ... other existing backends ...
]

# Add to MIDDLEWARE (append at the end)
MIDDLEWARE += ['label_studio_sso.middleware.JWTAutoLoginMiddleware']

# JWT SSO Configuration
JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'  # Claim containing user ID
JWT_SSO_COOKIE_NAME = 'ls_auth_token'  # Cookie-based (recommended)
JWT_SSO_COOKIE_PATH = '/'  # Cookie path (default: '/')
JWT_SSO_TOKEN_PARAM = 'token'  # URL parameter (fallback)

# API Configuration
SSO_TOKEN_EXPIRY = 600  # 10 minutes
SSO_AUTO_CREATE_USERS = True  # Auto-create users from API requests

# Important: If using reverse proxy, ensure cookies work across all paths
# CSRF_COOKIE_PATH = '/'  # Default is '/', do not change to '/label-studio'
# SESSION_COOKIE_PATH = '/'  # Default is '/', do not change to '/label-studio'
```

**Step 2: Add URL Patterns**

Edit `label_studio/core/urls.py` (or your main urls.py):

```python
# File: label_studio/core/urls.py
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('api/sso/', include('label_studio_sso.urls')),  # Add this line
]
```

**Step 3: Run Migrations (if needed)**

```bash
# Create database tables for rest_framework.authtoken
python label_studio/manage.py migrate
```

**Step 4: Create API Token for SSO**

```bash
# Option 1: Via Django admin
# 1. Login to Label Studio as admin
# 2. Go to Account Settings → Access Token
# 3. Copy the token

# Option 2: Via command line
python label_studio/manage.py drf_create_token <admin_username>
```

**Step 5: Restart Label Studio**

```bash
# If running via source
python label_studio/manage.py runserver

# If running via systemd
sudo systemctl restart label-studio

# If running via Docker
docker-compose restart
```

**Step 6: Verify Configuration**

```bash
# Test the SSO API endpoint
curl -X POST http://localhost:8080/api/sso/token \
  -H "Authorization: Token <your-label-studio-api-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Expected response:
# {"token": "eyJhbGc...", "expires_in": 600}
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
  path: '/',
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
  ↓ Request JWT token from Label Studio API
  ↓ POST /api/sso/token with user email
  ↓
Label Studio
  ↓ Verify API token (admin level)
  ↓ Generate JWT with user_id
  ↓ Return JWT token
  ↓
External System
  ↓ Set HttpOnly cookie with JWT (recommended)
  ↓ Or use URL parameter: ?token=eyJhbGc...
  ↓
User accesses Label Studio
  ↓ JWTAutoLoginMiddleware extracts token
  ↓ JWTAuthenticationBackend validates JWT
  ↓ User authenticated via user_id claim
  ✅ User logged in!
```

---

## 🔧 Usage Examples

### Example 1: Node.js/Express Integration

```javascript
const axios = require('axios');

// Get Label Studio admin API token from environment
const labelStudioApiToken = process.env.LABEL_STUDIO_API_TOKEN;

// Request JWT token from Label Studio
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

// Set HttpOnly cookie (recommended)
res.cookie('ls_auth_token', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  path: '/',
  maxAge: expires_in * 1000
});

// Redirect to Label Studio (clean URL!)
res.redirect('http://labelstudio.example.com/');
```

### Example 2: Python/Django Integration

```python
import requests

# Request JWT token from Label Studio
response = requests.post(
    'http://labelstudio.example.com/api/sso/token',
    json={'email': user.email},
    headers={
        'Authorization': f'Token {settings.LABEL_STUDIO_API_TOKEN}',
        'Content-Type': 'application/json'
    }
)

token_data = response.json()
token = token_data['token']
expires_in = token_data['expires_in']

# Set cookie and redirect
response = redirect('http://labelstudio.example.com/')
response.set_cookie(
    'ls_auth_token',
    token,
    httponly=True,
    secure=True,
    samesite='Strict',
    path='/',
    max_age=expires_in
)
return response
```

### Example 3: Reverse Proxy with Cookie Auto-Setup

For scenarios where Label Studio is embedded in an iframe:

```javascript
// Node.js/Koa reverse proxy
const axios = require('axios');

app.use('/label-studio', async (ctx, next) => {
  const user = ctx.state.user; // Already authenticated user

  if (user && !ctx.cookies.get('ls_auth_token')) {
    // Request JWT from Label Studio API
    const response = await axios.post(
      `${labelStudioUrl}/api/sso/token`,
      { email: user.email },
      {
        headers: {
          'Authorization': `Token ${process.env.LABEL_STUDIO_API_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );

    // Set JWT cookie
    ctx.cookies.set('ls_auth_token', response.data.token, {
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'Lax',
      maxAge: response.data.expires_in * 1000
    });
  }

  // Proxy to Label Studio
  await proxyToLabelStudio(ctx);
});
```

---

## ⚙️ Configuration Options

### JWT Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `JWT_SSO_NATIVE_USER_ID_CLAIM` | `user_id` | JWT claim containing user ID |
| `JWT_SSO_TOKEN_PARAM` | `token` | URL parameter name for JWT token |
| `JWT_SSO_COOKIE_NAME` | `None` | Cookie name for JWT token (recommended) |
| `JWT_SSO_COOKIE_PATH` | `/` | Cookie path - use `/` for all paths, not `/label-studio` |

### API Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `SSO_TOKEN_EXPIRY` | `600` | Token expiry time in seconds (10 minutes) |
| `SSO_AUTO_CREATE_USERS` | `True` | Auto-create users from API requests |

---

## 🔒 Security Best Practices

### 1. Protect API Tokens

Label Studio API tokens have admin privileges. Store them securely:

```bash
# Good: Use environment variables
export LABEL_STUDIO_API_TOKEN="<your-token>"

# Bad: Hardcode in source
LABEL_STUDIO_API_TOKEN = "hardcoded"  # ❌ Never do this
```

### 2. Use HTTPS Only

**Always use HTTPS** in production to protect tokens in transit.

### 3. Short Token Expiration

Use short-lived JWT tokens (default: 10 minutes):

```python
# Configure in Label Studio settings
SSO_TOKEN_EXPIRY = 600  # 10 minutes (recommended)
```

### 4. Use HttpOnly Cookies

Prefer HttpOnly cookies over URL parameters:

```javascript
// Good: HttpOnly cookie
res.cookie('ls_auth_token', token, {
  httpOnly: true,  // ✅ Cannot be accessed by JavaScript
  secure: true,
  sameSite: 'strict'
});

// Bad: URL parameter (legacy)
const url = `https://ls.example.com?token=${token}`;  // ⚠️ Visible in logs
```

### 5. Restrict API Token Access

Only admin-level API tokens can issue SSO tokens. Regularly rotate tokens and revoke unused ones.

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. "Module label_studio_sso not found"

**Problem**: Label Studio can't find the installed package.

**Solution**:
```bash
# Verify installation in the correct environment
pip list | grep label-studio-sso

# If not found, install it
pip install label-studio-sso

# Check Python environment matches Label Studio
which python
# Should match the Python used to run Label Studio
```

#### 2. "Authentication failed - No JWT token provided"

**Problem**: Token not being passed to Label Studio.

**Solution**:
```bash
# Check if token is in URL
echo "URL: http://labelstudio.example.com?token=YOUR_TOKEN"

# Check if cookie is being set
# In browser DevTools → Application → Cookies
# Look for 'ls_auth_token' cookie

# Verify middleware is enabled
python manage.py shell
>>> from django.conf import settings
>>> print('label_studio_sso.middleware.JWTAutoLoginMiddleware' in settings.MIDDLEWARE)
True
```

#### 3. "Invalid JWT signature"

**Problem**: JWT token verification failed.

**Solution**:
```bash
# Verify Label Studio's SECRET_KEY hasn't changed
python manage.py shell
>>> from django.conf import settings
>>> print(settings.SECRET_KEY)

# Ensure tokens are issued by the same Label Studio instance
```

#### 4. "User not found in Label Studio"

**Problem**: User doesn't exist in Label Studio.

**Solution**:
```python
# Option 1: Enable auto-create users
SSO_AUTO_CREATE_USERS = True

# Option 2: Manually create user in Label Studio
python manage.py createsuperuser
# Enter email that matches API request
```

#### 5. "API endpoint /api/sso/token returns 404"

**Problem**: URL patterns not configured.

**Solution**:
```python
# Check urls.py includes label_studio_sso.urls
from django.urls import path, include

urlpatterns = [
    path('api/sso/', include('label_studio_sso.urls')),  # Add this
]

# Restart Label Studio
# Test endpoint:
curl http://localhost:8080/api/sso/token
```

#### 6. "Token expired" errors

**Problem**: JWT token has expired.

**Solution**:
```python
# Configure longer expiration in Label Studio settings
SSO_TOKEN_EXPIRY = 1800  # 30 minutes

# Or request fresh tokens more frequently
```

#### 7. "401 Unauthorized" when calling /api/sso/token

**Problem**: Invalid or missing API token.

**Solution**:
```bash
# Verify API token is valid
curl -X POST http://localhost:8080/api/sso/token \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# If fails, generate new token
python manage.py drf_create_token <username>
```

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
# File: label_studio/core/settings/label_studio.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'label_studio_sso': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Enable debug logs
            'propagate': False,
        },
    },
}
```

Then check logs:
```bash
# You'll see detailed JWT authentication logs:
# [JWT Backend] Verifying native Label Studio JWT
# [JWT Backend] Native JWT auth successful: user@example.com
```

---

## 🧪 Testing

### Local Testing

```bash
# 1. Start Label Studio
cd /path/to/label-studio
python manage.py runserver

# 2. Create admin API token
python manage.py drf_create_token admin

# 3. Test SSO token endpoint
curl -X POST http://localhost:8080/api/sso/token \
  -H "Authorization: Token <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Expected response:
# {"token": "eyJhbGc...", "expires_in": 600}

# 4. Test authentication with JWT token
# Copy the token from step 3 and visit:
# http://localhost:8080?token=<jwt-token>

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
