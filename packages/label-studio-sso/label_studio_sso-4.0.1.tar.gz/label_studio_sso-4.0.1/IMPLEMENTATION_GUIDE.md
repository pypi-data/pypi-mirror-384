# label-studio-sso: 3가지 인증 방식 통합 구현 가이드

## 📋 목차

1. [개요](#개요)
2. [방식 1: 외부 JWT 토큰 인증](#방식-1-외부-jwt-토큰-인증)
3. [방식 2: Label Studio 네이티브 JWT 인증](#방식-2-label-studio-네이티브-jwt-인증)
4. [방식 3: 외부 세션 쿠키 인증](#방식-3-외부-세션-쿠키-인증)
5. [환경별 세션 공유 제약사항](#환경별-세션-공유-제약사항)
6. [설정 변수 완전 참조](#설정-변수-완전-참조)
7. [구현 예제](#구현-예제)

---

## 개요

### label-studio-sso의 목적

Label Studio UI를 외부 시스템(클라이언트)의 iframe/popup에 통합할 때,
사용자가 별도 로그인 없이 자동으로 인증되도록 하는 SSO(Single Sign-On) 솔루션.

> **💡 "SSO" 용어에 대하여**: 이 패키지는 전통적인 SSO(한 번 로그인 → 모든 서비스 접근)가 아닌, **인증 통합(Authentication Integration)**을 제공합니다. 하지만 업계 관례에 따라 "SSO"로 명명했으며, 사용자 관점에서는 Label Studio에 별도 로그인 없이 접근할 수 있어 SSO처럼 느껴집니다. 자세한 내용은 README.md의 "Understanding SSO" 섹션을 참조하세요.

### 지원하는 3가지 인증 방식

| 방식 | 설명 | 토큰 발급 주체 | 검증 방식 | 사용 사례 |
|------|------|--------------|---------|----------|
| **방식 1** | 외부 JWT | 클라이언트 | JWT 시크릿 검증 | 독립 시스템 SSO (권장) |
| **방식 2** | Label Studio JWT | Label Studio | Label Studio SECRET_KEY | Label Studio 토큰 재사용 |
| **방식 3** | 외부 세션 쿠키 | N/A (세션) | 클라이언트 API 호출 | 레거시 시스템 통합 |

---

## 방식 1: 외부 JWT 토큰 인증

### 개념

클라이언트가 자체 시크릿으로 JWT를 생성하고, label-studio-sso가 이를 검증하여 세션 생성.

### 블록 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│ 브라우저                                                              │
│                                                                     │
│  1. 사용자 로그인                                                    │
│     POST /login                                                     │
│     ↓                                                               │
│  2. Label Studio 메뉴 클릭                                           │
│     GET /open-labelstudio                                           │
│     ↓                                                               │
│  3. iframe 열기                                                      │
│     <iframe src="/label-studio?token=eyJhbGc...">                   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ GET /label-studio?token=eyJhbGc...
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ 클라이언트 시스템                                                      │
│                                                                     │
│  4. JWT 토큰 생성                                                    │
│     jwt.sign(                                                       │
│       { email: user.email, exp: now + 600 },                       │
│       JWT_SSO_SECRET,                                               │
│       { algorithm: 'HS256' }                                        │
│     )                                                               │
│     ↓                                                               │
│  5. 응답                                                             │
│     /label-studio?token=eyJhbGc...                                  │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ GET /label-studio?token=eyJhbGc...
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ label-studio-sso (Middleware)                                       │
│                                                                     │
│  6. 토큰 추출                                                        │
│     token = request.GET.get('token')                                │
│     or request.COOKIES.get('jwt_auth_token')                        │
│     ↓                                                               │
│  7. JWT 검증 (방식 1)                                                │
│     payload = jwt.decode(                                           │
│       token,                                                        │
│       settings.JWT_SSO_SECRET,  ← 클라이언트와 공유                  │
│       algorithms=[settings.JWT_SSO_ALGORITHM]                       │
│     )                                                               │
│     ↓                                                               │
│  8. 사용자 조회                                                      │
│     email = payload[settings.JWT_SSO_EMAIL_CLAIM]                   │
│     user = User.objects.get(email=email)                            │
│     ↓                                                               │
│  9. 세션 생성                                                        │
│     login(request, user)                                            │
│     Set-Cookie: sessionid=xyz789                                    │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ sessionid=xyz789
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ Label Studio                                                        │
│                                                                     │
│  10. 페이지 렌더링                                                   │
│      request.user = User(email='user@example.com')                 │
│      ✅ 인증 완료                                                    │
│                                                                     │
│  11. 이후 API 요청                                                   │
│      GET /api/projects                                              │
│      Cookie: sessionid=xyz789                                       │
│      → Django SessionMiddleware가 자동 인증                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 필수 설정 변수

#### Label Studio (settings.py)

```python
# label_studio/core/settings/base.py

# ============================================
# 방식 1: 외부 JWT 토큰 인증 설정
# ============================================

# [필수] 외부 시스템과 공유하는 JWT 시크릿
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
# 예: 'shared-secret-key-between-client-and-labelstudio'

# [선택] JWT 서명 알고리즘 (기본: HS256)
JWT_SSO_ALGORITHM = 'HS256'
# 지원: HS256, HS512, RS256, RS512

# [선택] URL 파라미터 이름 (기본: token)
JWT_SSO_TOKEN_PARAM = 'token'
# iframe src="/label-studio?token=xxx"에서 'token' 부분

# [선택] Cookie 이름 (기본: None, 비활성화)
JWT_SSO_COOKIE_NAME = 'jwt_auth_token'
# Cookie: jwt_auth_token=xxx
# None이면 Cookie 인증 비활성화

# [필수] JWT에서 이메일을 추출할 claim 이름
JWT_SSO_EMAIL_CLAIM = 'email'
# JWT payload: { "email": "user@example.com" }

# [선택] JWT에서 사용자명을 추출할 claim 이름 (기본: None, email 사용)
JWT_SSO_USERNAME_CLAIM = 'username'
# JWT payload: { "username": "johndoe" }
# None이면 email을 username으로 사용

# [선택] JWT에서 이름을 추출할 claim 이름
JWT_SSO_FIRST_NAME_CLAIM = 'first_name'
JWT_SSO_LAST_NAME_CLAIM = 'last_name'

# [선택] 사용자 자동 생성 여부 (기본: False)
JWT_SSO_AUTO_CREATE_USERS = False
# True: JWT 검증 성공 시 사용자 자동 생성
# False: 사용자가 Label Studio에 미리 존재해야 함 (권장)

# [선택] 세션 쿠키 도메인 (서브도메인 환경)
SESSION_COOKIE_DOMAIN = '.company.com'
# 서브도메인 간 쿠키 공유 시 필요
# 예: app.company.com ↔ labelstudio.company.com

# [선택] 세션 쿠키 SameSite 설정
SESSION_COOKIE_SAMESITE = 'Lax'  # 기본값
# Lax: Same-Site 및 Top-level navigation
# None: Cross-Site 허용 (HTTPS + Secure 필수)
# Strict: Same-Site만

# [선택] HTTPS 환경에서 Secure 쿠키
SESSION_COOKIE_SECURE = False  # HTTP 환경
# SESSION_COOKIE_SECURE = True  # HTTPS 환경
```

#### 클라이언트 시스템

```bash
# .env
JWT_SSO_SECRET=shared-secret-key-between-client-and-labelstudio
```

```typescript
// 클라이언트 백엔드
import jwt from 'jsonwebtoken'

export function generateLabelStudioToken(user: User): string {
  return jwt.sign(
    {
      email: user.email,
      username: user.username,
      first_name: user.firstName,
      last_name: user.lastName,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 600  // 10분
    },
    process.env.JWT_SSO_SECRET!,
    { algorithm: 'HS256' }
  )
}
```

### 장점

- ✅ 클라이언트가 인증 주도권 보유
- ✅ 단기 토큰 (5-10분) 보안
- ✅ 검증된 SSO 아키텍처
- ✅ 네트워크 호출 불필요 (로컬 검증)

### 단점

- ⚠️ 클라이언트와 시크릿 공유 필요
- ⚠️ JWT 라이브러리 필요

---

## 방식 2: Label Studio 네이티브 JWT 인증

### 개념

Label Studio가 자체 발급한 JWT(LSAPIToken)를 label-studio-sso가 검증하여 세션 생성.

### 블록 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│ 브라우저                                                              │
│                                                                     │
│  1. 사용자 로그인                                                    │
│     POST /login                                                     │
│     ↓                                                               │
│  2. Label Studio 메뉴 클릭                                           │
│     GET /open-labelstudio                                           │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ GET /api/get-labelstudio-token
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ 클라이언트 시스템                                                      │
│                                                                     │
│  3. Label Studio API 호출                                           │
│     POST http://label-studio:8080/api/current-user/token            │
│     Headers:                                                        │
│       Authorization: Token {ADMIN_API_KEY}                          │
│     Body:                                                           │
│       { email: "user@example.com" }                                 │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ POST /api/current-user/token
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ Label Studio (API)                                                  │
│                                                                     │
│  4. LSAPIToken 생성                                                 │
│     token = jwt.sign(                                               │
│       {                                                             │
│         user_id: 123,                                               │
│         email: "user@example.com",                                  │
│         exp: now + (200 * 365 * 86400)  # 200년!                   │
│       },                                                            │
│       settings.SECRET_KEY,  ← Label Studio 내부 시크릿              │
│       algorithm='HS256'                                             │
│     )                                                               │
│     ↓                                                               │
│  5. 응답                                                             │
│     { token: "eyJhbGc..." }                                         │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ { token: "eyJhbGc..." }
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ 클라이언트 시스템                                                      │
│                                                                     │
│  6. 브라우저로 리다이렉트                                             │
│     /label-studio?token=eyJhbGc...                                  │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ GET /label-studio?token=eyJhbGc...
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ label-studio-sso (Middleware)                                       │
│                                                                     │
│  7. 토큰 추출                                                        │
│     token = request.GET.get('token')                                │
│     ↓                                                               │
│  8. 외부 JWT 검증 시도 (방식 1)                                      │
│     if JWT_SSO_SECRET:                                              │
│       try: verify with JWT_SSO_SECRET                               │
│       except: pass  # 실패, 다음 시도                               │
│     ↓                                                               │
│  9. Label Studio JWT 검증 (방식 2) ✅                                │
│     if JWT_SSO_VERIFY_NATIVE_TOKEN:                                 │
│       payload = jwt.decode(                                         │
│         token,                                                      │
│         settings.SECRET_KEY,  ← Label Studio SECRET_KEY             │
│         algorithms=['HS256']                                        │
│       )                                                             │
│     ↓                                                               │
│  10. 사용자 조회                                                     │
│      user_id = payload['user_id']                                   │
│      user = User.objects.get(pk=user_id)                            │
│     ↓                                                               │
│  11. 세션 생성                                                       │
│      login(request, user)                                           │
│      Set-Cookie: sessionid=xyz789                                   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ sessionid=xyz789
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ Label Studio                                                        │
│                                                                     │
│  12. 페이지 렌더링                                                   │
│      ✅ 인증 완료                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 필수 설정 변수

#### Label Studio (settings.py)

```python
# label_studio/core/settings/base.py

# ============================================
# 방식 2: Label Studio 네이티브 JWT 인증 설정
# ============================================

# [필수] Label Studio 네이티브 JWT 검증 활성화
JWT_SSO_VERIFY_NATIVE_TOKEN = True
# True: Label Studio가 발급한 JWT 검증 가능
# False: 외부 JWT만 검증 (기본값)

# [선택] Label Studio JWT에서 user_id를 추출할 claim 이름
JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'
# Label Studio JWT 구조에 따라 조정
# 일반적으로 'user_id' 또는 'id'

# [선택] URL 파라미터 이름 (방식 1과 동일)
JWT_SSO_TOKEN_PARAM = 'token'

# [선택] Cookie 이름 (방식 1과 동일)
JWT_SSO_COOKIE_NAME = 'jwt_auth_token'

# [참고] Label Studio SECRET_KEY는 자동 사용됨
# settings.SECRET_KEY (Django 기본 설정)

# ⚠️ 보안 주의: SECRET_KEY 노출 위험
# Label Studio 내부 시크릿을 JWT 검증에 사용하므로
# 보안에 민감한 환경에서는 방식 1 권장
```

#### 클라이언트 시스템

```typescript
// 클라이언트 백엔드
async function getLabelStudioToken(userEmail: string): Promise<string> {
  const response = await fetch('http://label-studio:8080/api/current-user/token', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${process.env.LABEL_STUDIO_ADMIN_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email: userEmail })
  })

  const data = await response.json()
  return data.token  // Label Studio가 발급한 JWT
}
```

### 장점

- ✅ Label Studio 기존 토큰 시스템 활용
- ✅ 별도 JWT 발급 로직 불필요
- ✅ Label Studio 토큰 관리 체계 사용

### 단점

- ⚠️ Label Studio SECRET_KEY 노출
- ⚠️ LSAPIToken 기본 수명 200년 (보안 주의)
- ⚠️ 관리자 API 키 필요

---

## 방식 3: 외부 세션 쿠키 인증

### 개념

클라이언트의 세션 쿠키를 label-studio-sso가 받아서 클라이언트 API로 검증하여 세션 생성.

### 블록 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│ 브라우저                                                              │
│                                                                     │
│  1. 사용자 로그인                                                    │
│     POST /login                                                     │
│     ↓                                                               │
│  2. 클라이언트 세션 생성                                             │
│     Set-Cookie: sessionid=abc123; Domain=.company.com               │
│     ↓                                                               │
│  3. Label Studio 메뉴 클릭                                           │
│     GET /label-studio/projects/1                                    │
│     Cookie: sessionid=abc123  ← 브라우저가 자동 전송                 │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ GET /label-studio?...
                       │ Cookie: sessionid=abc123
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ Reverse Proxy (nginx)                                               │
│                                                                     │
│  4. 쿠키 전달                                                        │
│     proxy_set_header Cookie $http_cookie;                           │
│     ↓                                                               │
│  5. Label Studio로 프록시                                            │
│     → http://label-studio:8080                                      │
│       Cookie: sessionid=abc123                                      │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ GET /projects/1
                       │ Cookie: sessionid=abc123
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ label-studio-sso (Middleware)                                       │
│                                                                     │
│  6. 세션 쿠키 추출                                                   │
│     session_cookie = request.COOKIES.get(                           │
│       settings.JWT_SSO_SESSION_COOKIE_NAME  # 'sessionid'           │
│     )                                                               │
│     ↓                                                               │
│  7. 외부 JWT/Native JWT 검증 시도                                    │
│     if JWT_SSO_SECRET or JWT_SSO_VERIFY_NATIVE_TOKEN:               │
│       try: verify JWT                                               │
│       except: pass  # 실패, 다음 시도                               │
│     ↓                                                               │
│  8. 세션 쿠키 검증 (방식 3) ✅                                        │
│     if JWT_SSO_SESSION_VERIFY_URL and session_cookie:               │
│       # 클라이언트 API 호출                                          │
│       response = requests.get(                                      │
│         settings.JWT_SSO_SESSION_VERIFY_URL,                        │
│         cookies={'sessionid': session_cookie},                      │
│         headers={'X-Verify-Token': settings.JWT_SSO_SESSION_VERIFY_SECRET},
│         timeout=5                                                   │
│       )                                                             │
│     ↓                                                               │
│  9. 사용자 정보 추출                                                 │
│     user_data = response.json()                                     │
│     # { email, username, first_name, last_name }                    │
│     ↓                                                               │
│  10. 사용자 조회/생성                                                │
│      user = User.objects.get_or_create(                             │
│        email=user_data['email'],                                    │
│        defaults={...}                                               │
│      )                                                              │
│     ↓                                                               │
│  11. 세션 생성                                                       │
│      login(request, user)                                           │
│      Set-Cookie: ls_sessionid=xyz789                                │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       │ ls_sessionid=xyz789
                       │
┌──────────────────────▼──────────────────────────────────────────────┐
│ Label Studio                                                        │
│                                                                     │
│  12. 페이지 렌더링                                                   │
│      ✅ 인증 완료                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 클라이언트 API 상세

```
┌──────────────────────▼──────────────────────────────────────────────┐
│ 클라이언트 시스템 (세션 검증 API)                                      │
│                                                                     │
│  8-1. 요청 수신                                                      │
│       GET /api/auth/verify-session                                  │
│       Cookie: sessionid=abc123                                      │
│       Headers:                                                      │
│         X-Verify-Token: shared-verify-secret                        │
│       ↓                                                             │
│  8-2. 검증 토큰 확인                                                 │
│       if req.headers['X-Verify-Token'] != VERIFY_SECRET:            │
│         return 401 Unauthorized                                     │
│       ↓                                                             │
│  8-3. 세션 검증                                                      │
│       session = SessionStore.get(sessionid='abc123')                │
│       user = User.objects.get(pk=session['_auth_user_id'])          │
│       ↓                                                             │
│  8-4. 사용자 정보 반환                                               │
│       return {                                                      │
│         email: user.email,                                          │
│         username: user.username,                                    │
│         first_name: user.first_name,                                │
│         last_name: user.last_name,                                  │
│         id: user.id                                                 │
│       }                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 필수 설정 변수

#### Label Studio (settings.py)

```python
# label_studio/core/settings/base.py

# ============================================
# 방식 3: 외부 세션 쿠키 인증 설정
# ============================================

# [필수] 세션 검증 API URL
JWT_SSO_SESSION_VERIFY_URL = 'http://client-api:3000/api/auth/verify-session'
# 클라이언트 세션을 검증할 API 엔드포인트
# Label Studio가 이 API를 호출하여 세션 유효성 확인

# [필수] 세션 검증 API 인증 토큰
JWT_SSO_SESSION_VERIFY_SECRET = os.getenv('JWT_SSO_SESSION_VERIFY_SECRET')
# X-Verify-Token 헤더에 전송될 시크릿
# 클라이언트 API가 Label Studio의 요청임을 확인하는 용도

# [선택] 클라이언트 세션 쿠키 이름
JWT_SSO_SESSION_COOKIE_NAME = 'sessionid'
# 클라이언트 시스템의 세션 쿠키 이름
# Django: 'sessionid' (기본)
# Express: 'connect.sid'
# Spring: 'JSESSIONID'

# [선택] 세션 검증 타임아웃 (초)
JWT_SSO_SESSION_VERIFY_TIMEOUT = 5
# 클라이언트 API 호출 타임아웃

# [선택] 세션 검증 결과 캐싱 (초)
JWT_SSO_SESSION_CACHE_TTL = 300  # 5분
# 동일 세션에 대한 반복 API 호출 방지
# 0이면 캐싱 비활성화

# [선택] 세션 검증 응답에서 추출할 필드
JWT_SSO_SESSION_EMAIL_FIELD = 'email'
JWT_SSO_SESSION_USERNAME_FIELD = 'username'
JWT_SSO_SESSION_FIRST_NAME_FIELD = 'first_name'
JWT_SSO_SESSION_LAST_NAME_FIELD = 'last_name'

# [선택] 사용자 자동 생성
JWT_SSO_SESSION_AUTO_CREATE_USERS = True
# 세션 검증 성공 시 사용자 자동 생성 (일반적으로 True)
```

#### 클라이언트 시스템

```bash
# .env
JWT_SSO_SESSION_VERIFY_SECRET=shared-verify-secret-between-systems
```

```typescript
// 클라이언트 백엔드: /api/auth/verify-session
import { Router } from 'express'

const router = Router()

router.get('/api/auth/verify-session', async (req, res) => {
  // 1. 검증 토큰 확인
  const verifyToken = req.headers['x-verify-token']
  if (verifyToken !== process.env.JWT_SSO_SESSION_VERIFY_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' })
  }

  // 2. 세션 쿠키에서 사용자 조회
  const sessionId = req.cookies.sessionid
  if (!sessionId) {
    return res.status(401).json({ error: 'No session' })
  }

  const user = await getUserFromSession(sessionId)
  if (!user) {
    return res.status(401).json({ error: 'Invalid session' })
  }

  // 3. 사용자 정보 반환
  return res.json({
    email: user.email,
    username: user.username,
    first_name: user.firstName,
    last_name: user.lastName,
    id: user.id
  })
})

export default router
```

#### Reverse Proxy (nginx)

```nginx
# nginx.conf

server {
    listen 80;
    server_name company.com;

    # 클라이언트
    location / {
        proxy_pass http://client:3000;
        proxy_set_header Cookie $http_cookie;
    }

    # Label Studio
    location /label-studio {
        proxy_pass http://label-studio:8080;

        # ✅ 핵심: 클라이언트 세션 쿠키 전달
        proxy_set_header Cookie $http_cookie;

        # 경로 재작성
        rewrite ^/label-studio(.*)$ $1 break;

        # Set-Cookie 경로 수정
        proxy_cookie_path / /label-studio;
    }
}
```

### 장점

- ✅ JWT 발급 불필요
- ✅ 클라이언트 세션 직접 활용
- ✅ 레거시 시스템 통합 용이

### 단점

- ⚠️ 클라이언트 API 구현 필수
- ⚠️ 네트워크 호출 오버헤드
- ⚠️ Reverse Proxy 필수
- ⚠️ 세션 검증 API 장애 시 영향

---

## 환경별 세션 공유 제약사항

### 1. Same Domain 환경

```
클라이언트:    http://company.com
Label Studio:  http://company.com/label-studio
```

#### 제약사항

| 항목 | 제약 | 설명 |
|------|------|------|
| **쿠키 전송** | ✅ 자동 | 같은 도메인이므로 자동 전송 |
| **SameSite** | ✅ Lax | 기본값으로 작동 |
| **HTTPS** | ⚠️ 선택 | HTTP도 가능 |
| **Proxy** | ⚠️ 선택 | URL 라우팅만 필요 |

#### 설정

```python
# Label Studio
SESSION_COOKIE_DOMAIN = None  # 기본값 (현재 도메인)
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # HTTP 환경
```

#### 동작

```
브라우저 → http://company.com/label-studio?token=xxx
  Cookie: 자동 전송 ✅
  SameSite=Lax: 허용 ✅
  Result: 완벽하게 작동 ✅
```

---

### 2. Subdomain 환경

```
클라이언트:    http://app.company.com
Label Studio:  http://labelstudio.company.com
```

#### 제약사항

| 항목 | 제약 | 설명 |
|------|------|------|
| **쿠키 전송** | ⚠️ 설정 필요 | SESSION_COOKIE_DOMAIN 설정 |
| **SameSite** | ✅ Lax | Same-Site로 인식 |
| **HTTPS** | ⚠️ 선택 | HTTP도 가능 |
| **Proxy** | ❌ 불필요 | 서브도메인 자체로 가능 |

#### 설정

```python
# Label Studio (핵심!)
SESSION_COOKIE_DOMAIN = '.company.com'  # ← 점(.) 필수!
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # HTTP 환경

# 클라이언트도 동일하게
SESSION_COOKIE_DOMAIN = '.company.com'
```

#### 동작

```
브라우저 → http://app.company.com
  Set-Cookie: sessionid=abc; Domain=.company.com

브라우저 → http://labelstudio.company.com?token=xxx
  Cookie: sessionid=abc ✅ (Domain=.company.com이므로)
  SameSite=Lax: Same-Site ✅ (company.com 동일)
  Result: 완벽하게 작동 ✅
```

#### 보안 주의사항

```python
# ⚠️ 위험: 모든 서브도메인에서 쿠키 접근 가능
SESSION_COOKIE_DOMAIN = '.company.com'
# → evil.company.com에서도 접근 가능!

# 대책:
# 1. 서브도메인 생성 권한 엄격히 제한
# 2. HTTPS + Secure 플래그
# 3. HttpOnly 플래그 (JavaScript 접근 차단)
# 4. 정기 세션 만료
```

---

### 3. Cross-Domain + HTTP + Proxy 환경

```
클라이언트:    http://client.com
Label Studio:  http://labelstudio.com
Proxy:         http://company.com
```

#### 제약사항

| 항목 | 제약 | 설명 |
|------|------|------|
| **쿠키 전송** | ✅ Proxy 필요 | Proxy로 Same Domain화 |
| **SameSite** | ✅ Lax | Proxy 경유 시 Same Domain |
| **HTTPS** | ❌ 불필요 | HTTP 가능 |
| **Proxy** | ✅ 필수 | 반드시 필요 |

#### Proxy 설정

```nginx
# nginx.conf
server {
    listen 80;
    server_name company.com;

    # 클라이언트
    location / {
        proxy_pass http://client.com:3000;
        proxy_set_header Cookie $http_cookie;
    }

    # Label Studio
    location /label-studio {
        proxy_pass http://labelstudio.com:8080;
        proxy_set_header Cookie $http_cookie;  # ← 핵심!

        rewrite ^/label-studio(.*)$ $1 break;
        proxy_cookie_path / /label-studio;
    }
}
```

#### 설정

```python
# Label Studio
SESSION_COOKIE_DOMAIN = None  # company.com (Proxy 도메인)
SESSION_COOKIE_PATH = '/label-studio'  # Proxy 경로
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
```

#### 동작

```
브라우저 → http://company.com
  Set-Cookie: sessionid=abc; Path=/

브라우저 → http://company.com/label-studio?token=xxx
  Cookie: sessionid=abc ✅ (Same Domain)
  Proxy → http://labelstudio.com:8080
  Cookie: sessionid=abc ✅ (Proxy 전달)
  Result: 완벽하게 작동 ✅
```

---

### 4. Cross-Domain + HTTP + No Proxy 환경

```
클라이언트:    http://client.com
Label Studio:  http://labelstudio.com
```

#### 제약사항

| 항목 | 제약 | 설명 |
|------|------|------|
| **쿠키 전송** | ❌ 불가능 | SameSite 차단 |
| **SameSite** | ❌ Lax 차단 | Cross-Site 차단 |
| **HTTPS** | ❌ 없음 | SameSite=None 불가 |
| **Proxy** | ❌ 없음 | Same Domain화 불가 |

#### 동작

```
브라우저 → http://client.com
  Set-Cookie: sessionid=abc; SameSite=Lax

브라우저 (iframe) → http://labelstudio.com?token=xxx
  Cookie: sessionid=abc ❌ (Cross-Site 차단!)

  최초 로드:
    JWT 검증 ✅
    Set-Cookie: ls_sessionid=xyz

  iframe 내부 요청:
    Cookie: ls_sessionid=xyz ❌ (Cross-Site 차단!)

  Result: 세션 작동 불가 ❌
```

#### 해결 방법

```
❌ 불가능: 방법 없음
✅ 해결책: Proxy 또는 HTTPS 사용 필수
```

---

### 5. Cross-Domain + HTTPS 환경

```
클라이언트:    https://client.com
Label Studio:  https://labelstudio.com
```

#### 제약사항

| 항목 | 제약 | 설명 |
|------|------|------|
| **쿠키 전송** | ✅ 가능 | SameSite=None |
| **SameSite** | ✅ None | HTTPS + Secure 필수 |
| **HTTPS** | ✅ 필수 | Secure 플래그 |
| **Proxy** | ❌ 불필요 | SameSite=None으로 해결 |

#### 설정

```python
# Label Studio (핵심!)
SESSION_COOKIE_SAMESITE = 'None'  # ← Cross-Site 허용
SESSION_COOKIE_SECURE = True  # ← HTTPS 필수!
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True

# CORS 설정
CORS_ALLOWED_ORIGINS = [
    'https://client.com',
]
CORS_ALLOW_CREDENTIALS = True
```

#### 동작

```
브라우저 → https://client.com
  Set-Cookie: sessionid=abc; SameSite=Lax

브라우저 (iframe) → https://labelstudio.com?token=xxx
  최초 로드:
    JWT 검증 ✅
    Set-Cookie: ls_sessionid=xyz; SameSite=None; Secure

  iframe 내부 요청:
    Cookie: ls_sessionid=xyz ✅ (SameSite=None + Secure)

  Result: 완벽하게 작동 ✅
```

---

### 환경별 요약 매트릭스

| 환경 | 방식 1 | 방식 2 | 방식 3 | 필수 설정 |
|------|--------|--------|--------|----------|
| **Same Domain (HTTP)** | ✅ | ✅ | ✅ | 없음 |
| **Subdomain (HTTP)** | ✅ | ✅ | ✅ | `SESSION_COOKIE_DOMAIN = '.company.com'` |
| **Cross-Domain (HTTP + Proxy)** | ✅ | ✅ | ✅ | Proxy Cookie 전달 |
| **Cross-Domain (HTTP, No Proxy)** | ⚠️ URL만 | ⚠️ URL만 | ❌ | 불가능 |
| **Cross-Domain (HTTPS)** | ✅ | ✅ | ✅ | `SameSite=None; Secure` |

---

## 설정 변수 완전 참조

### Django Settings (settings.py)

```python
# label_studio/core/settings/base.py

# ============================================
# label-studio-sso 기본 설정
# ============================================

INSTALLED_APPS = [
    # ... existing apps ...
    'label_studio_sso',
]

AUTHENTICATION_BACKENDS = [
    'label_studio_sso.backends.JWTAuthenticationBackend',
    'rules.permissions.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # ✅ label-studio-sso 미들웨어 (AuthenticationMiddleware 다음)
    'label_studio_sso.middleware.JWTAutoLoginMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# 방식 1: 외부 JWT 토큰 인증
# ============================================

# JWT 시크릿 (클라이언트와 공유)
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET', None)
# 예: 'shared-secret-key'
# None이면 방식 1 비활성화

# JWT 알고리즘
JWT_SSO_ALGORITHM = os.getenv('JWT_SSO_ALGORITHM', 'HS256')
# 지원: HS256, HS512, RS256, RS512

# URL 파라미터 이름
JWT_SSO_TOKEN_PARAM = os.getenv('JWT_SSO_TOKEN_PARAM', 'token')
# ?token=xxx

# Cookie 이름 (선택)
JWT_SSO_COOKIE_NAME = os.getenv('JWT_SSO_COOKIE_NAME', None)
# 'jwt_auth_token' 또는 None

# JWT Claim 매핑
JWT_SSO_EMAIL_CLAIM = os.getenv('JWT_SSO_EMAIL_CLAIM', 'email')
JWT_SSO_USERNAME_CLAIM = os.getenv('JWT_SSO_USERNAME_CLAIM', None)
JWT_SSO_FIRST_NAME_CLAIM = os.getenv('JWT_SSO_FIRST_NAME_CLAIM', 'first_name')
JWT_SSO_LAST_NAME_CLAIM = os.getenv('JWT_SSO_LAST_NAME_CLAIM', 'last_name')

# 사용자 자동 생성
JWT_SSO_AUTO_CREATE_USERS = os.getenv('JWT_SSO_AUTO_CREATE_USERS', 'false').lower() == 'true'

# ============================================
# 방식 2: Label Studio 네이티브 JWT
# ============================================

# Label Studio JWT 검증 활성화
JWT_SSO_VERIFY_NATIVE_TOKEN = os.getenv('JWT_SSO_VERIFY_NATIVE_TOKEN', 'false').lower() == 'true'

# Label Studio JWT user_id claim
JWT_SSO_NATIVE_USER_ID_CLAIM = os.getenv('JWT_SSO_NATIVE_USER_ID_CLAIM', 'user_id')

# ============================================
# 방식 3: 외부 세션 쿠키 인증
# ============================================

# 세션 검증 API URL
JWT_SSO_SESSION_VERIFY_URL = os.getenv('JWT_SSO_SESSION_VERIFY_URL', None)
# 'http://client-api:3000/api/auth/verify-session'

# 세션 검증 시크릿
JWT_SSO_SESSION_VERIFY_SECRET = os.getenv('JWT_SSO_SESSION_VERIFY_SECRET', None)

# 클라이언트 세션 쿠키 이름
JWT_SSO_SESSION_COOKIE_NAME = os.getenv('JWT_SSO_SESSION_COOKIE_NAME', 'sessionid')

# 세션 검증 타임아웃 (초)
JWT_SSO_SESSION_VERIFY_TIMEOUT = int(os.getenv('JWT_SSO_SESSION_VERIFY_TIMEOUT', '5'))

# 세션 검증 캐싱 TTL (초)
JWT_SSO_SESSION_CACHE_TTL = int(os.getenv('JWT_SSO_SESSION_CACHE_TTL', '300'))

# 세션 응답 필드 매핑
JWT_SSO_SESSION_EMAIL_FIELD = os.getenv('JWT_SSO_SESSION_EMAIL_FIELD', 'email')
JWT_SSO_SESSION_USERNAME_FIELD = os.getenv('JWT_SSO_SESSION_USERNAME_FIELD', 'username')
JWT_SSO_SESSION_FIRST_NAME_FIELD = os.getenv('JWT_SSO_SESSION_FIRST_NAME_FIELD', 'first_name')
JWT_SSO_SESSION_LAST_NAME_FIELD = os.getenv('JWT_SSO_SESSION_LAST_NAME_FIELD', 'last_name')

# 사용자 자동 생성
JWT_SSO_SESSION_AUTO_CREATE_USERS = os.getenv('JWT_SSO_SESSION_AUTO_CREATE_USERS', 'true').lower() == 'true'

# ============================================
# Django 세션 설정
# ============================================

# 세션 쿠키 도메인 (서브도메인 환경)
SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN', None)
# '.company.com' 또는 None (현재 도메인)

# 세션 쿠키 경로
SESSION_COOKIE_PATH = os.getenv('SESSION_COOKIE_PATH', '/')

# 세션 쿠키 SameSite
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
# 'Lax', 'Strict', 'None'

# 세션 쿠키 Secure (HTTPS)
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

# 세션 쿠키 HttpOnly
SESSION_COOKIE_HTTPONLY = True  # 보안상 권장

# ============================================
# CSRF 설정
# ============================================

CSRF_COOKIE_DOMAIN = SESSION_COOKIE_DOMAIN
CSRF_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_COOKIE_HTTPONLY = False  # JavaScript에서 읽어야 함

# ============================================
# CORS 설정
# ============================================

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
# ['https://client.com', 'https://app.company.com']

CORS_ALLOW_CREDENTIALS = True  # 쿠키 전송 허용
```

### 환경 변수 (.env)

```bash
# ============================================
# 방식 1: 외부 JWT
# ============================================
JWT_SSO_SECRET=shared-secret-key-between-client-and-labelstudio
JWT_SSO_ALGORITHM=HS256
JWT_SSO_TOKEN_PARAM=token
JWT_SSO_COOKIE_NAME=jwt_auth_token
JWT_SSO_EMAIL_CLAIM=email
JWT_SSO_USERNAME_CLAIM=username
JWT_SSO_AUTO_CREATE_USERS=false

# ============================================
# 방식 2: Label Studio 네이티브 JWT
# ============================================
JWT_SSO_VERIFY_NATIVE_TOKEN=true
JWT_SSO_NATIVE_USER_ID_CLAIM=user_id

# ============================================
# 방식 3: 외부 세션 쿠키
# ============================================
JWT_SSO_SESSION_VERIFY_URL=http://client-api:3000/api/auth/verify-session
JWT_SSO_SESSION_VERIFY_SECRET=shared-verify-secret
JWT_SSO_SESSION_COOKIE_NAME=sessionid
JWT_SSO_SESSION_VERIFY_TIMEOUT=5
JWT_SSO_SESSION_CACHE_TTL=300
JWT_SSO_SESSION_AUTO_CREATE_USERS=true

# ============================================
# 세션 쿠키 설정
# ============================================
SESSION_COOKIE_DOMAIN=.company.com
SESSION_COOKIE_PATH=/
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SECURE=false

# ============================================
# CORS
# ============================================
CORS_ALLOWED_ORIGINS=https://client.com,https://app.company.com
```

---

## 구현 예제

### 예제 1: 독립 시스템 SSO (방식 1)

#### 시나리오
- 클라이언트: Node.js (Express)
- Label Studio: 독립 배포
- 환경: 서브도메인 (app.company.com ↔ labelstudio.company.com)

#### Label Studio 설정

```python
# .env
JWT_SSO_SECRET=my-super-secret-key-12345
SESSION_COOKIE_DOMAIN=.company.com
```

```python
# settings.py
JWT_SSO_SECRET = os.getenv('JWT_SSO_SECRET')
JWT_SSO_TOKEN_PARAM = 'token'
JWT_SSO_COOKIE_NAME = 'jwt_auth_token'
JWT_SSO_EMAIL_CLAIM = 'email'
SESSION_COOKIE_DOMAIN = '.company.com'
SESSION_COOKIE_SAMESITE = 'Lax'
```

#### 클라이언트 구현

```typescript
// 백엔드: /api/label-studio/generate-token
import jwt from 'jsonwebtoken'

router.post('/api/label-studio/generate-token', async (req, res) => {
  const user = req.user

  const token = jwt.sign(
    {
      email: user.email,
      username: user.username,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 600
    },
    process.env.JWT_SSO_SECRET,
    { algorithm: 'HS256' }
  )

  res.json({ token })
})

// 프론트엔드
async function openLabelStudio() {
  const { token } = await fetch('/api/label-studio/generate-token', {
    method: 'POST'
  }).then(r => r.json())

  window.open(`https://labelstudio.company.com?token=${token}`, '_blank')
}
```

---

### 예제 2: Label Studio JWT 재사용 (방식 2)

#### 시나리오
- Label Studio API를 이미 사용 중
- Label Studio JWT를 UI에도 재사용

#### Label Studio 설정

```python
# .env
JWT_SSO_VERIFY_NATIVE_TOKEN=true
```

```python
# settings.py
JWT_SSO_VERIFY_NATIVE_TOKEN = True
JWT_SSO_NATIVE_USER_ID_CLAIM = 'user_id'
JWT_SSO_TOKEN_PARAM = 'token'
```

#### 클라이언트 구현

```typescript
// 백엔드
router.post('/api/label-studio/get-token', async (req, res) => {
  const user = req.user

  const response = await fetch('http://labelstudio:8080/api/current-user/token', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${process.env.LABEL_STUDIO_ADMIN_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email: user.email })
  })

  const data = await response.json()
  res.json({ token: data.token })
})

// 프론트엔드
async function openLabelStudio() {
  const { token } = await fetch('/api/label-studio/get-token', {
    method: 'POST'
  }).then(r => r.json())

  window.open(`https://labelstudio.company.com?token=${token}`, '_blank')
}
```

---

### 예제 3: 레거시 세션 통합 (방식 3)

#### 시나리오
- 레거시 Django 클라이언트
- 세션 기반 인증
- Reverse Proxy 사용

#### Label Studio 설정

```python
# .env
JWT_SSO_SESSION_VERIFY_URL=http://client-api:3000/api/auth/verify-session
JWT_SSO_SESSION_VERIFY_SECRET=verify-secret-abc123
SESSION_COOKIE_DOMAIN=.company.com
```

```python
# settings.py
JWT_SSO_SESSION_VERIFY_URL = os.getenv('JWT_SSO_SESSION_VERIFY_URL')
JWT_SSO_SESSION_VERIFY_SECRET = os.getenv('JWT_SSO_SESSION_VERIFY_SECRET')
JWT_SSO_SESSION_COOKIE_NAME = 'sessionid'
JWT_SSO_SESSION_AUTO_CREATE_USERS = True
SESSION_COOKIE_DOMAIN = '.company.com'
```

#### 클라이언트 세션 검증 API

```python
# Django 클라이언트: views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def verify_session(request):
    # 검증 토큰 확인
    verify_token = request.headers.get('X-Verify-Token')
    if verify_token != settings.JWT_SSO_SESSION_VERIFY_SECRET:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    # 세션에서 사용자 조회
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    # 사용자 정보 반환
    return JsonResponse({
        'email': request.user.email,
        'username': request.user.username,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'id': request.user.id
    })
```

#### nginx 설정

```nginx
server {
    listen 80;
    server_name company.com;

    location / {
        proxy_pass http://client:3000;
        proxy_set_header Cookie $http_cookie;
    }

    location /label-studio {
        proxy_pass http://labelstudio:8080;
        proxy_set_header Cookie $http_cookie;
        rewrite ^/label-studio(.*)$ $1 break;
        proxy_cookie_path / /label-studio;
    }
}
```

---

## 요약

### 3가지 방식 선택 가이드

```
독립 시스템 SSO:
  → 방식 1 (외부 JWT) ✅ 권장

Label Studio 토큰 재사용:
  → 방식 2 (Label Studio JWT)

레거시 세션 통합:
  → 방식 3 (외부 세션 쿠키)
```

### 환경별 필수 설정

```
Same Domain:
  → 추가 설정 불필요

Subdomain:
  → SESSION_COOKIE_DOMAIN = '.company.com'

Cross-Domain (HTTP):
  → Reverse Proxy 필수

Cross-Domain (HTTPS):
  → SameSite=None; Secure
```

### label-studio-sso 구현 우선순위

```
1단계: 방식 1 (외부 JWT) ✅ 완료
2단계: 방식 2 (Label Studio JWT) 🔄 구현 중
3단계: 방식 3 (외부 세션 쿠키) 📋 계획
```

---

**이 문서는 label-studio-sso 패키지의 3가지 인증 방식 구현을 위한 완전한 가이드입니다.** 🎉
