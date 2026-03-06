# MaxHub API Documentation

**Base URL:** `http://42.96.20.12:8000`
**Version:** 1.0.0
**Auth:** JWT Bearer token (`Authorization: Bearer <token>`)

---

## Authentication

### POST `/api/register`

Đăng ký tài khoản mới.

**Auth:** Không cần

**Request body:**
```json
{
  "username": "string (3-100 ký tự)",
  "password": "string (6-255 ký tự)"
}
```

**Response:**
```json
{ "ok": true, "message": "Dang ky thanh cong." }
```

**Errors:**
| Case | Response |
|------|----------|
| Username đã tồn tại | `{ "ok": false, "message": "Ten dang nhap da ton tai." }` |
| Username < 3 ký tự | HTTP 422 Validation Error |
| Password < 6 ký tự | HTTP 422 Validation Error |

---

### POST `/api/login`

Đăng nhập và nhận JWT token.

**Auth:** Không cần

**Request body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (thành công):**
```json
{
  "ok": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "username": "admin",
  "role": "admin"
}
```

**Errors:**
| Case | Response |
|------|----------|
| Username không tồn tại | `{ "ok": false, "message": "Ten dang nhap khong ton tai." }` |
| Tài khoản bị khoá | `{ "ok": false, "message": "Tai khoan da bi khoa." }` |
| Sai mật khẩu | `{ "ok": false, "message": "Mat khau khong dung." }` |

**Notes:**
- Token có hiệu lực 72 giờ (configurable via `JWT_EXPIRE_HOURS` env)
- `last_login_at` được cập nhật mỗi lần login
- JWT payload: `{ sub: user_id, username, role, tv: token_version, exp }`

---

## User Profile

### GET `/api/me`

Lấy thông tin tài khoản hiện tại.

**Auth:** Bearer token (bắt buộc)

**Response:**
```json
{
  "ok": true,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "presence": "online",
  "bio": "Hello world!",
  "created_at": "2026-03-05 10:30:00+00:00",
  "last_login_at": "2026-03-06 08:15:00+00:00"
}
```

**Errors:**
| Case | HTTP | Message |
|------|------|---------|
| Thiếu token | 422 | Field required |
| Token hết hạn | 401 | Token het han. |
| Token không hợp lệ | 401 | Token khong hop le. |
| User bị xoá | 401 | User not found. |
| User bị khoá | 403 | Tai khoan bi khoa. |
| Token bị thu hồi (đổi mật khẩu) | 401 | Token da bi thu hoi. |

---

### PUT `/api/me`

Cập nhật thông tin profile. Chỉ gửi các field muốn thay đổi.

**Auth:** Bearer token (bắt buộc)

**Request body (tất cả optional):**
```json
{
  "email": "user@example.com",
  "presence": "online",
  "bio": "Đang bận việc..."
}
```

**Fields:**

| Field | Type | Validation | Mô tả |
|-------|------|-----------|-------|
| `email` | string \| null | max 255 chars | Địa chỉ email |
| `presence` | string \| null | `online`, `busy`, `away`, `dnd`, `invisible` | Trạng thái hiện diện |
| `bio` | string \| null | max 500 chars | Suy nghĩ / mô tả ngắn |

**Response:**
```json
{ "ok": true, "message": "Cap nhat thanh cong." }
```

**Errors:**
| Case | Response |
|------|----------|
| Không có field nào thay đổi | `{ "ok": true, "message": "Khong co thay doi." }` |
| Presence không hợp lệ | HTTP 422 Validation Error |
| Bio > 500 ký tự | HTTP 422 Validation Error |

---

### PUT `/api/me/password`

Đổi mật khẩu. Sau khi đổi, `token_version` tăng 1 → token cũ bị vô hiệu hoá.

**Auth:** Bearer token (bắt buộc)

**Request body:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password_min_6_chars"
}
```

**Response:**
```json
{ "ok": true, "message": "Doi mat khau thanh cong." }
```

**Errors:**
| Case | Response |
|------|----------|
| Sai mật khẩu hiện tại | `{ "ok": false, "message": "Mat khau hien tai khong dung." }` |
| Mật khẩu mới < 6 ký tự | HTTP 422 Validation Error |

**Notes:**
- `token_version` tăng → tất cả token cũ đều bị thu hồi
- Client phải đăng nhập lại sau khi đổi mật khẩu

---

## System

### GET `/api/health`

Kiểm tra server còn sống.

**Auth:** Không cần

**Response:**
```json
{ "ok": true, "service": "maxhub-api" }
```

---

### GET `/api/version`

Kiểm tra phiên bản app mới nhất (dùng cho auto-update).

**Auth:** Không cần

**Response:**
```json
{
  "version": "1.0.0",
  "update_url": "https://example.com/MaxHub-Setup.exe",
  "force": false
}
```

**Fields:**

| Field | Type | Mô tả |
|-------|------|-------|
| `version` | string | Phiên bản mới nhất |
| `update_url` | string | URL tải file .exe cập nhật |
| `force` | boolean | `true` = bắt buộc cập nhật, không cho skip |

---

## Database Schema

```sql
CREATE TABLE users (
    id             BIGSERIAL PRIMARY KEY,
    username       VARCHAR(100) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    email          VARCHAR(255),
    role           VARCHAR(50) DEFAULT 'user',
    status         VARCHAR(50) DEFAULT 'active',
    presence       VARCHAR(20) DEFAULT 'online',
    bio            VARCHAR(500) DEFAULT '',
    token_version  BIGINT DEFAULT 0,
    last_login_at  TIMESTAMPTZ,
    last_login_ip  VARCHAR(50),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW(),
    deleted_at     TIMESTAMPTZ
);
```

**Roles:** `user`, `admin`, `moderator`
**Status:** `active`, `inactive`, `banned`
**Presence:** `online`, `busy`, `away`, `dnd`, `invisible`

---

## Environment Variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `DB_HOST` | localhost | PostgreSQL host |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_NAME` | maxhub | Database name |
| `DB_USER` | postgres | Database user |
| `DB_PASSWORD` | (empty) | Database password |
| `JWT_SECRET` | change-me | Secret key cho JWT signing |
| `JWT_EXPIRE_HOURS` | 72 | Thời gian hết hạn token (giờ) |
| `APP_VERSION` | 1.0.0 | Phiên bản app hiện tại |
| `UPDATE_URL` | (empty) | URL file cập nhật .exe |

---

## Client Usage (Python)

```python
from utils.api import api

# Auth
ok, msg = api.register("username", "password")
ok, msg = api.login("username", "password")

# Profile
ok, data = api.me()            # GET /api/me
ok, data = api.get("/api/me")  # same

# Update profile
ok, data = api.put("/api/me", {"email": "a@b.com", "presence": "busy"})

# Change password
ok, data = api.put("/api/me/password", {
    "current_password": "old",
    "new_password": "new123"
})

# Session persistence
api.save_session()     # Lưu JWT vào QSettings
api.restore_session()  # Đọc JWT từ QSettings
api.clear_session()    # Xoá session
api.logout()           # Xoá token + session

# Properties
api.is_logged_in  # bool
api.username      # str | None
api.role          # str | None
api.token         # str | None
```
