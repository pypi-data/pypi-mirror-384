# Label Studio SSO - 설정 가이드

이 문서는 다양한 환경에서 `label-studio-sso`를 설정하는 방법을 설명합니다.

`label-studio-sso`는 3가지 인증 방식을 지원합니다:
1. **외부 JWT 토큰 인증** (기본, 권장)
2. **Label Studio 네이티브 JWT 인증** (Label Studio JWT 재사용)
3. **외부 세션 쿠키 인증** (레거시 시스템 통합)

---

## 📋 설정 옵션

### 방식 1: 외부 JWT 토큰 인증 (기본)

#### 필수 설정

| 설정 변수 | 설명 | 예시 |
|----------|------|------|
| `JWT_SSO_SECRET` | JWT 서명 검증용 공유 시크릿 키 | `"your-secret-key-here"` |

#### 선택 설정

| 설정 변수 | 기본값 | 설명 | 예시 |
|----------|--------|------|------|
| `JWT_SSO_ALGORITHM` | `HS256` | JWT 서명 알고리즘 | `HS256`, `HS512`, `RS256` |
| `JWT_SSO_TOKEN_PARAM` | `token` | URL에서 토큰을 추출할 파라미터 이름 | `token`, `jwt`, `auth_token` |
| `JWT_SSO_COOKIE_NAME` | `None` | Cookie에서 토큰을 추출할 쿠키 이름 (Reverse Proxy용) | `jwt_auth_token`, `sso_token` |
| `JWT_SSO_EMAIL_CLAIM` | `email` | JWT에서 이메일을 추출할 claim 이름 | `email`, `user_email`, `mail` |
| `JWT_SSO_USERNAME_CLAIM` | `None` | JWT에서 사용자명을 추출할 claim 이름 (None이면 email 사용) | `username`, `sub`, `user_id` |
| `JWT_SSO_FIRST_NAME_CLAIM` | `first_name` | 이름 claim | `first_name`, `given_name`, `fname` |
| `JWT_SSO_LAST_NAME_CLAIM` | `last_name` | 성 claim | `last_name`, `family_name`, `surname` |
| `JWT_SSO_AUTO_CREATE_USERS` | `False` | 사용자가 없으면 자동 생성 | `True`, `False` |

### 방식 2: Label Studio 네이티브 JWT 인증

| 설정 변수 | 기본값 | 설명 | 예시 |
|----------|--------|------|------|
| `JWT_SSO_VERIFY_NATIVE_TOKEN` | `False` | Label Studio JWT 검증 활성화 | `True` |
| `JWT_SSO_NATIVE_USER_ID_CLAIM` | `user_id` | 사용자 ID claim 이름 | `user_id`, `sub` |
| `JWT_SSO_TOKEN_PARAM` | `token` | URL 파라미터 이름 | `token`, `key` |
| `JWT_SSO_COOKIE_NAME` | `None` | Cookie 이름 (선택) | `jwt_token` |

**참고**: 이 방식은 `JWT_SSO_SECRET` 대신 Label Studio의 `SECRET_KEY`를 사용합니다.

### 방식 3: 외부 세션 쿠키 인증

#### 필수 설정

| 설정 변수 | 설명 | 예시 |
|----------|------|------|
| `JWT_SSO_SESSION_VERIFY_URL` | 클라이언트 API 세션 검증 엔드포인트 | `http://client-api:3000/api/auth/verify-session` |
| `JWT_SSO_SESSION_VERIFY_SECRET` | API 인증용 공유 시크릿 | `"shared-secret-key"` |

#### 선택 설정

| 설정 변수 | 기본값 | 설명 | 예시 |
|----------|--------|------|------|
| `JWT_SSO_SESSION_COOKIE_NAME` | `sessionid` | 세션 쿠키 이름 | `sessionid`, `connect.sid` |
| `JWT_SSO_SESSION_VERIFY_TIMEOUT` | `5` | API 요청 타임아웃 (초) | `5`, `10` |
| `JWT_SSO_SESSION_CACHE_TTL` | `300` | 세션 검증 캐시 TTL (초) | `300`, `600` |
| `JWT_SSO_SESSION_AUTO_CREATE_USERS` | `True` | 사용자 자동 생성 | `True`, `False` |

---

## 🎯 사용 사례별 설정

### 방식 1: 외부 JWT 토큰 인증

#### 사례 1-1: Client Application 통합 (Reverse Proxy 방식)

**JWT 토큰 구조**:
```json
{
  "email": "user@example.com",
  "username": "user@example.com",
  "iat": 1234567890,
  "exp": 1234567900
}
```

**Label Studio 설정** (Cookie 기반):
```python
# settings.py
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')  # Client Application와 동일한 시크릿
JWT_SSO_ALGORITHM = 'HS256'
JWT_SSO_COOKIE_NAME = 'jwt_auth_token'  # Cookie 인증 활성화
JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_USERNAME_CLAIM = 'username'
JWT_SSO_AUTO_CREATE_USERS = False  # Client Application에서 사용자 동기화 사용
```

**Label Studio 설정** (URL 파라미터 방식):
```python
# settings.py
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
JWT_SSO_ALGORITHM = 'HS256'
JWT_SSO_TOKEN_PARAM = 'token'  # URL 파라미터 인증
JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_AUTO_CREATE_USERS = False
```

**Label Studio 설정** (하이브리드 방식 - 권장):
```python
# settings.py
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
JWT_SSO_ALGORITHM = 'HS256'
JWT_SSO_TOKEN_PARAM = 'token'          # URL 우선
JWT_SSO_COOKIE_NAME = 'jwt_auth_token' # Cookie 폴백
JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_AUTO_CREATE_USERS = False
```

---

#### 사례 1-2: Auth0 통합

**JWT 토큰 구조**:
```json
{
  "email": "user@example.com",
  "sub": "auth0|123456",
  "given_name": "John",
  "family_name": "Doe",
  "iat": 1234567890,
  "exp": 1234567900
}
```

**Label Studio 설정**:
```python
# settings.py
JWT_SSO_SECRET = os.getenv('AUTH0_JWT_SECRET')
JWT_SSO_ALGORITHM = 'HS256'
JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_USERNAME_CLAIM = 'sub'
JWT_SSO_FIRST_NAME_CLAIM = 'given_name'
JWT_SSO_LAST_NAME_CLAIM = 'family_name'
JWT_SSO_AUTO_CREATE_USERS = True  # Auth0에서 자동 생성
```

---

#### 사례 1-3: Keycloak 통합

**JWT 토큰 구조**:
```json
{
  "email": "user@example.com",
  "preferred_username": "john.doe",
  "given_name": "John",
  "family_name": "Doe",
  "iat": 1234567890,
  "exp": 1234567900
}
```

**Label Studio 설정**:
```python
# settings.py
JWT_SSO_SECRET = os.getenv('KEYCLOAK_JWT_SECRET')
JWT_SSO_ALGORITHM = 'RS256'  # Keycloak은 보통 RS256 사용
JWT_SSO_EMAIL_CLAIM = 'email'
JWT_SSO_USERNAME_CLAIM = 'preferred_username'
JWT_SSO_FIRST_NAME_CLAIM = 'given_name'
JWT_SSO_LAST_NAME_CLAIM = 'family_name'
JWT_SSO_AUTO_CREATE_USERS = True
```

---

#### 사례 1-4: 커스텀 시스템 통합

**JWT 토큰 구조** (예시):
```json
{
  "user_email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "iat": 1234567890,
  "exp": 1234567900
}
```

**Label Studio 설정**:
```python
# settings.py
JWT_SSO_SECRET = os.getenv('CUSTOM_JWT_SECRET')
JWT_SSO_ALGORITHM = 'HS256'
JWT_SSO_EMAIL_CLAIM = 'user_email'
JWT_SSO_USERNAME_CLAIM = 'username'
JWT_SSO_FIRST_NAME_CLAIM = 'full_name'  # full_name을 first_name에 매핑
JWT_SSO_AUTO_CREATE_USERS = True
```

---

### 방식 2: Label Studio 네이티브 JWT 인증

#### 사례 2-1: Label Studio JWT 재사용

클라이언트가 Label Studio API를 통해 JWT 토큰을 받아 iframe에서 재사용하는 경우.

**Label Studio 설정**:
```python
# settings.py
JWT_SSO_VERIFY_NATIVE_TOKEN = True
JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'
JWT_SSO_TOKEN_PARAM = 'token'
```

**클라이언트 구현**:
```javascript
// 1. Label Studio API에서 JWT 받기
const response = await fetch('http://labelstudio.example.com/api/current-user/token', {
  headers: {
    'Authorization': `Token ${ADMIN_API_KEY}`
  }
});
const { token } = await response.json();

// 2. iframe으로 Label Studio 열기
const iframe = document.createElement('iframe');
iframe.src = `http://labelstudio.example.com?token=${token}`;
document.body.appendChild(iframe);
```

**장점**:
- 별도 JWT 시크릿 관리 불필요
- Label Studio 기존 인증 체계 재사용

---

### 방식 3: 외부 세션 쿠키 인증

#### 사례 3-1: 레거시 Django 시스템 통합

기존 Django 시스템의 세션 쿠키를 Label Studio에서도 사용하는 경우.

**Label Studio 설정**:
```python
# settings.py
JWT_SSO_SESSION_VERIFY_URL = 'http://legacy-system:3000/api/auth/verify-session'
JWT_SSO_SESSION_VERIFY_SECRET = os.getenv('SESSION_VERIFY_SECRET')
JWT_SSO_SESSION_COOKIE_NAME = 'sessionid'  # Django 기본 세션 쿠키
JWT_SSO_SESSION_VERIFY_TIMEOUT = 5
JWT_SSO_SESSION_CACHE_TTL = 300  # 5분 캐시
JWT_SSO_SESSION_AUTO_CREATE_USERS = True

# 서브도메인 쿠키 공유 설정
SESSION_COOKIE_DOMAIN = '.example.com'  # 점(.) 필수!
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_DOMAIN = '.example.com'

# CORS 설정
CORS_ALLOWED_ORIGINS = ['http://app.example.com']
CORS_ALLOW_CREDENTIALS = True
```

**클라이언트 API 구현** (`/api/auth/verify-session`):
```javascript
// Node.js + Express 예시
app.post('/api/auth/verify-session', (req, res) => {
  const authHeader = req.headers.authorization;
  const secret = process.env.SESSION_VERIFY_SECRET;

  // 1. 공유 시크릿 검증
  if (authHeader !== `Bearer ${secret}`) {
    return res.status(401).json({ valid: false });
  }

  // 2. 세션 쿠키 추출
  const sessionCookie = req.body.session_cookie;

  // 3. 세션 검증 (Redis, DB 등)
  const session = await getSessionFromStore(sessionCookie);

  if (!session || !session.user) {
    return res.json({ valid: false });
  }

  // 4. 사용자 정보 반환
  res.json({
    valid: true,
    email: session.user.email,
    username: session.user.username,
    first_name: session.user.firstName,
    last_name: session.user.lastName
  });
});
```

**장점**:
- JWT 토큰 생성 불필요
- 기존 세션 관리 체계 재사용
- 실시간 세션 유효성 검증

**제약사항**:
- 클라이언트 API 구현 필요
- 서브도메인 환경 필요 (같은 루트 도메인)
- 또는 Reverse Proxy로 쿠키 전달 필요

---

#### 사례 3-2: Node.js Express 세션 통합

**Label Studio 설정**:
```python
# settings.py
JWT_SSO_SESSION_VERIFY_URL = 'http://nodejs-app:4000/api/verify'
JWT_SSO_SESSION_VERIFY_SECRET = os.getenv('SESSION_SECRET')
JWT_SSO_SESSION_COOKIE_NAME = 'connect.sid'  # Express 기본 쿠키
JWT_SSO_SESSION_AUTO_CREATE_USERS = True

SESSION_COOKIE_DOMAIN = '.company.com'
```

**Node.js API**:
```javascript
const session = require('express-session');
const RedisStore = require('connect-redis')(session);

app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET,
  name: 'connect.sid',
  cookie: { domain: '.company.com' }  // 서브도메인 공유
}));

app.post('/api/verify', async (req, res) => {
  // 세션 검증 로직
  const sessionId = req.body.session_cookie;
  const sessionData = await redisClient.get(`sess:${sessionId}`);

  if (!sessionData) {
    return res.json({ valid: false });
  }

  const session = JSON.parse(sessionData);
  res.json({
    valid: true,
    email: session.user.email,
    username: session.user.username,
    first_name: session.user.firstName,
    last_name: session.user.lastName
  });
});
```

---

## 🔐 보안 설정

### 1. JWT 시크릿 생성

**권장 방법**:
```python
import secrets
secret = secrets.token_urlsafe(32)
print(f"JWT_SSO_SECRET={secret}")
```

**결과 예시**:
```
JWT_SSO_SECRET=6Xo9d8fK3jN2hT5vL1mP4wQ7rY0eU9aZ3bC6sD8gH2k
```

### 2. HTTPS 필수

JWT 토큰이 URL 파라미터로 전달되므로 **반드시 HTTPS를 사용**해야 합니다.

```nginx
# nginx 설정 예시
server {
    listen 443 ssl;
    server_name label-studio.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
    }
}
```

### 3. 토큰 유효 기간

**권장 설정**: 5-10분

```python
# 외부 시스템에서 토큰 생성 시
from datetime import datetime, timedelta

token = jwt.encode({
    'email': 'user@example.com',
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(minutes=5)  # 5분 유효
}, secret, algorithm='HS256')
```

### 4. CORS 설정

Label Studio에서 iframe 임베딩을 허용해야 합니다:

```python
# Label Studio settings.py
CORS_ALLOWED_ORIGINS = [
    'https://your-portal.example.com',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'  # 또는 특정 도메인 허용
```

---

## 🧪 테스트 설정

### 로컬 개발 환경

```bash
# .env.local
JWT_SSO_SECRET="test-secret-key-for-development"
JWT_SSO_ALGORITHM="HS256"
JWT_SSO_EMAIL_CLAIM="email"
JWT_SSO_AUTO_CREATE_USERS="true"
```

### 테스트 토큰 생성 스크립트

```python
# generate_test_token.py
import jwt
from datetime import datetime, timedelta

SECRET = "test-secret-key-for-development"

def generate_token(email, first_name="", last_name="", minutes=10):
    payload = {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=minutes)
    }
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    return token

if __name__ == '__main__':
    token = generate_token('test@example.com', 'John', 'Doe')
    print(f"Test URL: http://localhost:8080?token={token}")
```

---

## 🔧 트러블슈팅

### 문제 1: "JWT_SSO_SECRET is not configured"

**원인**: 환경 변수가 설정되지 않음

**해결**:
```bash
export JWT_SSO_SECRET="your-secret-key"
# 또는 .env 파일에 추가
```

### 문제 2: "JWT token does not contain 'email' claim"

**원인**: JWT 토큰에 email claim이 없거나 이름이 다름

**해결**:
```python
# JWT 토큰 구조 확인
import jwt
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)  # claim 이름 확인

# 설정 조정
JWT_SSO_EMAIL_CLAIM = 'user_email'  # 실제 claim 이름으로 변경
```

### 문제 3: "User not found in Label Studio"

**원인**: 사용자가 Label Studio에 존재하지 않음

**해결 방법 1**: 자동 생성 활성화
```python
JWT_SSO_AUTO_CREATE_USERS = True
```

**해결 방법 2**: 수동으로 사용자 생성
```bash
python manage.py createsuperuser --email user@example.com
```

### 문제 4: "JWT token signature verification failed"

**원인**: JWT 시크릿이 일치하지 않음

**해결**:
1. 외부 시스템과 Label Studio의 `JWT_SSO_SECRET`이 동일한지 확인
2. 알고리즘(`JWT_SSO_ALGORITHM`)이 일치하는지 확인

---

## 📊 모니터링

### 로그 설정

```python
# Label Studio settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/label-studio/sso.log',
        },
    },
    'loggers': {
        'label_studio_sso': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### 주요 로그 메시지

```
# 성공
INFO: JWT token verified for email: user@example.com
INFO: User found: user@example.com
INFO: User auto-logged in: user@example.com

# 실패
WARNING: JWT token has expired
ERROR: JWT token signature verification failed
WARNING: User not found in Label Studio: user@example.com
```

---

## 📚 참고 자료

- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Django Authentication Backends](https://docs.djangoproject.com/en/stable/topics/auth/customizing/)
- [JWT.io - JWT Debugger](https://jwt.io/)
