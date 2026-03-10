# Goserver - Authentication API

Web service Go chuẩn cấu trúc Clean Architecture, cung cấp API xác thực người dùng.

## Chức năng

- Đăng ký / Đăng nhập (email + password)
- Đổi mật khẩu
- Đăng xuất
- OAuth: Google, Facebook
- JWT + Session Cookie (dual auth)
- Rate limiting
- CORS

## Cấu trúc thư mục

```
Goserver/
├── cmd/server/main.go              # Entry point
├── internal/
│   ├── config/config.go            # Load env config
│   ├── database/
│   │   ├── postgres.go             # PostgreSQL connection
│   │   └── migration.go            # Auto migration
│   ├── model/user.go               # Structs & DTOs
│   ├── repository/user_repo.go     # Database queries
│   ├── service/
│   │   ├── auth_service.go         # Auth business logic
│   │   ├── oauth_service.go        # Google + Facebook OAuth
│   │   └── email_service.go        # Password reset email
│   ├── handler/
│   │   ├── auth_handler.go         # HTTP handlers - auth
│   │   └── oauth_handler.go        # HTTP handlers - OAuth
│   └── middleware/
│       ├── auth.go                 # JWT/Session middleware
│       └── ratelimit.go            # Rate limiting
├── pkg/utils/
│   ├── hash.go                     # bcrypt, token generation
│   └── http.go                     # CORS, error recovery
├── docs/
│   └── api-design.md               # API design document
├── .env.example
├── go.mod
└── go.sum
```

## Kiến trúc

```
Request → CORS → RecoverErrors → RateLimit → Handler → Service → Repository → PostgreSQL
```

## Cài đặt & Chạy

### 1. Yêu cầu

- Go 1.24+
- PostgreSQL

### 2. Cấu hình

```bash
cp .env.example .env
# Sửa .env với thông tin database và OAuth credentials
```

### 3. Chạy

```bash
go run cmd/server/main.go
```

Server khởi động tại `http://localhost:8080`

## API Endpoints

### Public

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/auth/register` | Đăng ký tài khoản |
| POST | `/api/auth/login` | Đăng nhập |
| GET | `/api/auth/google` | Đăng nhập Google |
| GET | `/api/auth/google/callback` | Google OAuth callback |
| GET | `/api/auth/facebook` | Đăng nhập Facebook |
| GET | `/api/auth/facebook/callback` | Facebook OAuth callback |

### Protected (cần JWT hoặc Session)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/auth/change-password` | Đổi mật khẩu |
| POST | `/api/auth/logout` | Đăng xuất |

## Ví dụ sử dụng

### Đăng ký

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "MyPassword123"}'
```

### Đăng nhập

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "MyPassword123"}'
```

### Đổi mật khẩu

```bash
curl -X POST http://localhost:8080/api/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"old_password": "MyPassword123", "new_password": "NewPassword456"}'
```

## Cấu hình (.env)

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `SERVER_PORT` | Port server | `8080` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | DB user | `postgres` |
| `DB_PASSWORD` | DB password | `secret` |
| `DB_NAME` | DB name | `goserver` |
| `JWT_SECRET` | JWT signing key | - |
| `JWT_EXPIRY` | JWT token expiry | `24h` |
| `SESSION_EXPIRY` | Session cookie expiry | `168h` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | - |
| `FACEBOOK_CLIENT_ID` | Facebook OAuth client ID | - |
| `FACEBOOK_CLIENT_SECRET` | Facebook OAuth secret | - |
| `FRONTEND_URL` | Frontend URL cho OAuth redirect | `http://localhost:3000` |

## Rate Limiting

| Endpoint | Giới hạn |
|----------|---------|
| `/api/auth/login` | 5 requests / phút / IP |
| `/api/auth/register` | 3 requests / phút / IP |

## Bảo mật

- Password hash: bcrypt (DefaultCost)
- JWT: HS256, 24h expiry
- Session: HttpOnly, Secure, SameSite=Strict
- OAuth: CSRF state token protection
- Rate limiting trên login/register
- CORS headers
- Panic recovery middleware
