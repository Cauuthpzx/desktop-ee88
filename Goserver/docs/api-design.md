# Goserver API Design Document

## Tổng quan

Web service Go với chức năng xác thực người dùng: đăng ký, đăng nhập, đổi mật khẩu, OAuth (Google, Facebook).

## Kiến trúc

```
HTTP Request → Handler → Service → Repository → PostgreSQL
```

**Cấu trúc thư mục:**

```
Goserver/
├── cmd/server/main.go
├── internal/
│   ├── config/config.go
│   ├── model/user.go
│   ├── repository/user_repo.go
│   ├── service/
│   │   ├── auth_service.go
│   │   └── oauth_service.go
│   ├── handler/
│   │   ├── auth_handler.go
│   │   └── oauth_handler.go
│   ├── middleware/
│   │   ├── auth.go
│   │   └── ratelimit.go
│   └── database/
│       ├── postgres.go
│       └── migration.go
├── pkg/utils/hash.go
├── go.mod
└── .env.example
```

---

## API Endpoints

### Base URL: `/api`

---

### 1. Đăng ký - Register

```
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "MyPassword123"
}
```

**Validation:**
- `email`: required, valid email format, unique
- `password`: required, min 8 ký tự

**Success Response (201):**
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "created_at": "2026-03-10T10:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Error Responses:**

| Code | Trường hợp |
|------|-----------|
| 400  | Thiếu field hoặc validation fail |
| 409  | Email đã tồn tại |
| 500  | Server error |

```json
{
  "status": "error",
  "message": "email already exists"
}
```

---

### 2. Đăng nhập - Login

```
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "MyPassword123"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com"
    },
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

Response cũng set cookie:
```
Set-Cookie: session=<session_cookie>; HttpOnly; Secure; SameSite=Strict; Path=/
```

**Error Responses:**

| Code | Trường hợp |
|------|-----------|
| 400  | Thiếu field |
| 401  | Email hoặc password sai |
| 429  | Rate limit exceeded |
| 500  | Server error |

---

### 3. Đổi mật khẩu - Change Password

```
POST /api/auth/change-password
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "old_password": "MyPassword123",
  "new_password": "NewPassword456"
}
```

**Validation:**
- `old_password`: required
- `new_password`: required, min 8 ký tự, khác old_password

**Success Response (200):**
```json
{
  "status": "success",
  "message": "password changed successfully"
}
```

**Side effects:**
- Xóa tất cả sessions cũ (buộc đăng nhập lại trên các thiết bị khác)

**Error Responses:**

| Code | Trường hợp |
|------|-----------|
| 400  | Validation fail |
| 401  | Chưa đăng nhập hoặc token hết hạn |
| 403  | Old password sai |
| 500  | Server error |

---

### 4. Đăng xuất - Logout

```
POST /api/auth/logout
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "logged out successfully"
}
```

**Side effects:**
- Xóa session cookie
- Invalidate session trong DB

---

### 5. Google OAuth

```
GET /api/auth/google
```
→ Redirect tới Google OAuth consent screen

```
GET /api/auth/google/callback?code=xxx&state=yyy
```

**Success:** Redirect tới frontend với JWT token
```
302 → {FRONTEND_URL}/auth/callback?token=eyJ...
```

**Error:** Redirect với error
```
302 → {FRONTEND_URL}/auth/callback?error=oauth_failed
```

---

### 6. Facebook OAuth

```
GET /api/auth/facebook
```
→ Redirect tới Facebook OAuth

```
GET /api/auth/facebook/callback?code=xxx&state=yyy
```

**Success/Error:** Tương tự Google OAuth

---

## Data Models

### User
| Field      | Type      | Constraint          |
|-----------|-----------|---------------------|
| id        | BIGSERIAL | PRIMARY KEY         |
| email     | TEXT      | UNIQUE, NOT NULL    |
| password  | TEXT      | nullable (OAuth users) |
| settings  | TEXT      | nullable            |
| created_at| TIMESTAMP | NOT NULL            |
| last_seen | TIMESTAMP | NOT NULL            |

### Session
| Field     | Type      | Constraint          |
|----------|-----------|---------------------|
| cookie   | TEXT      | PRIMARY KEY         |
| user_id  | BIGINT    | FK → Users          |
| last_used| TIMESTAMP | NOT NULL            |

### OAuth
| Field      | Type   | Constraint              |
|-----------|--------|-------------------------|
| method    | TEXT   | NOT NULL                |
| foreign_id| TEXT   | NOT NULL                |
| token     | TEXT   | nullable                |
| user_id   | BIGINT | FK → Users, NOT NULL    |
| UNIQUE    |        | (method, foreign_id)    |

---

## Authentication

### JWT
- Algorithm: HS256
- Expiry: 24h
- Payload: `{ user_id, email, exp, iat }`
- Dùng cho API requests qua header `Authorization: Bearer <token>`

### Session Cookie
- HttpOnly, Secure, SameSite=Strict
- Expiry: 7 ngày
- Dùng cho web browser

---

## Middleware

### Auth Middleware
- Kiểm tra JWT token từ `Authorization` header
- Hoặc kiểm tra session cookie
- Inject user info vào request context

### Rate Limit
- Login: 5 requests / phút / IP
- Register: 3 requests / phút / IP
- Change password: 3 requests / phút / user

---

## Config (.env)

```env
SERVER_PORT=8080
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=secret
DB_NAME=goserver
JWT_SECRET=your-secret-key
JWT_EXPIRY=24h
SESSION_EXPIRY=168h
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URL=http://localhost:8080/api/auth/google/callback
FACEBOOK_CLIENT_ID=xxx
FACEBOOK_CLIENT_SECRET=xxx
FACEBOOK_REDIRECT_URL=http://localhost:8080/api/auth/facebook/callback
FRONTEND_URL=http://localhost:3000
```
