# Migration Guide: v5.0.0 → v6.0.0

## Breaking Changes Summary

Version 6.0.0 removes **Method 1 (External JWT)** where client applications generated JWT tokens with a shared secret. Only **Method 2 (Native JWT)** is now supported, where Label Studio issues tokens via its API.

## Why This Change?

1. **Security**: No shared secrets between systems
2. **Simplicity**: No JWT library needed on client side
3. **Centralized Control**: Label Studio manages all token issuance
4. **Better Architecture**: Single authentication method, easier to maintain

## Migration Steps

### Step 1: Check Your Current Setup

If your Label Studio settings include any of these, you're using Method 1:

```python
JWT_SSO_SECRET = "..."
JWT_SSO_ALGORITHM = "..."
JWT_SSO_EMAIL_CLAIM = "..."
JWT_SSO_USERNAME_CLAIM = "..."
JWT_SSO_AUTO_CREATE_USERS = True/False
```

### Step 2: Update Label Studio Settings

**Remove** Method 1 settings:
```python
# ❌ REMOVE THESE
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
JWT_SSO_ALGORITHM = 'HS256'
JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_USERNAME_CLAIM = 'username'
JWT_SSO_FIRST_NAME_CLAIM = 'first_name'
JWT_SSO_LAST_NAME_CLAIM = 'last_name'
JWT_SSO_AUTO_CREATE_USERS = True
JWT_SSO_VERIFY_NATIVE_TOKEN = True  # No longer needed
```

**Add** Method 2 settings:
```python
# ✅ ADD THESE
INSTALLED_APPS += [
    'rest_framework',
    'rest_framework.authtoken',
]

JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'
JWT_SSO_COOKIE_NAME = 'ls_auth_token'
JWT_SSO_TOKEN_PARAM = 'token'

SSO_TOKEN_EXPIRY = 600  # 10 minutes
SSO_AUTO_CREATE_USERS = True
```

### Step 3: Add URL Patterns

Add SSO API endpoint to your `label_studio/core/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('api/sso/', include('label_studio_sso.urls')),
]
```

### Step 4: Update Client Code

**Before (Method 1 - Client generates JWT):**
```javascript
const jwt = require('jsonwebtoken');

// Client generated JWT with shared secret
const token = jwt.sign(
  {
    email: 'user@example.com',
    exp: Math.floor(Date.now() / 1000) + 600
  },
  process.env.JWT_SSO_SECRET,  // ❌ Shared secret
  { algorithm: 'HS256' }
);

// Pass token to Label Studio
res.redirect(`http://labelstudio.example.com?token=${token}`);
```

**After (Method 2 - Label Studio issues JWT):**
```javascript
const axios = require('axios');

// Request JWT from Label Studio API
const response = await axios.post(
  'http://labelstudio.example.com/api/sso/token',
  { email: 'user@example.com' },
  {
    headers: {
      'Authorization': `Token ${process.env.LABEL_STUDIO_API_TOKEN}`,
      'Content-Type': 'application/json'
    }
  }
);

const { token, expires_in } = response.data;

// Set secure HttpOnly cookie
res.cookie('ls_auth_token', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  maxAge: expires_in * 1000
});

// Redirect to Label Studio
res.redirect('http://labelstudio.example.com/');
```

### Step 5: Create Label Studio API Token

Create an admin API token for SSO token issuance:

```bash
# Option 1: Via Django admin
# Login to Label Studio → Account Settings → Access Token

# Option 2: Via command line
python label_studio/manage.py drf_create_token <admin_username>
```

Store this token securely in your environment:

```bash
export LABEL_STUDIO_API_TOKEN="your-admin-api-token"
```

### Step 6: Run Migrations

```bash
cd /path/to/label-studio
python manage.py migrate
```

### Step 7: Restart Label Studio

```bash
# Source installation
python label_studio/manage.py runserver

# Systemd
sudo systemctl restart label-studio

# Docker
docker-compose restart
```

### Step 8: Test

```bash
# Test the SSO API endpoint
curl -X POST http://localhost:8080/api/sso/token \
  -H "Authorization: Token <your-api-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Expected response:
# {"token": "eyJhbGc...", "expires_in": 600}
```

## Benefits of Method 2

✅ **No Shared Secrets**: Label Studio's SECRET_KEY stays private
✅ **Simpler Client**: No JWT library needed, just HTTP requests
✅ **Centralized Control**: Token issuance fully controlled by Label Studio
✅ **Better Security**: Admin-level API token required for token issuance
✅ **Less Configuration**: 8 fewer configuration variables

## Removed Settings

The following settings are no longer used:

- `JWT_SSO_SECRET` - Uses Label Studio's SECRET_KEY
- `JWT_SSO_ALGORITHM` - Always uses HS256
- `JWT_SSO_EMAIL_CLAIM` - Uses user_id instead
- `JWT_SSO_USERNAME_CLAIM` - Uses user_id instead
- `JWT_SSO_FIRST_NAME_CLAIM` - Not used in Method 2
- `JWT_SSO_LAST_NAME_CLAIM` - Not used in Method 2
- `JWT_SSO_AUTO_CREATE_USERS` - Moved to `SSO_AUTO_CREATE_USERS`
- `JWT_SSO_VERIFY_NATIVE_TOKEN` - Always native now

## New Settings

- `JWT_SSO_NATIVE_USER_ID_CLAIM` - Default: 'user_id'
- `SSO_TOKEN_EXPIRY` - Default: 600 (seconds)
- `SSO_AUTO_CREATE_USERS` - Default: True

## Need Help?

- **Documentation**: [README.md](./README.md)
- **Changelog**: [CHANGELOG.md](./CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/aidoop/label-studio-sso/issues)

## Rollback

If you need to rollback to v5.0.0:

```bash
pip install label-studio-sso==5.0.0
```

Note: v5.0.0 will receive security updates only. All new features will be in v6.0.0+.
