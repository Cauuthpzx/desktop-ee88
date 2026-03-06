"""
utils/auth.py
Xác thực người dùng — tạo bảng, đăng ký, đăng nhập.

Dùng:
    from utils.auth import auth

    auth.init()                              # tạo bảng users (gọi 1 lần khi khởi app)
    ok, msg = auth.register("admin", "123456")
    ok, msg = auth.login("admin", "123456")
"""
from __future__ import annotations

import logging

import bcrypt

from utils.db import Database

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id             BIGSERIAL PRIMARY KEY,
    username       VARCHAR(100) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    email          VARCHAR(255),
    role           VARCHAR(50) DEFAULT 'user',
    status         VARCHAR(50) DEFAULT 'active',
    token_version  BIGINT DEFAULT 0,
    last_login_at  TIMESTAMPTZ,
    last_login_ip  VARCHAR(50),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW(),
    deleted_at     TIMESTAMPTZ
);
"""


class AuthService:
    def init(self) -> None:
        """Tạo bảng users nếu chưa có."""
        try:
            with Database() as db:
                db.execute(_CREATE_TABLE)
        except Exception as e:
            logger.error("auth.init failed: %s", e, exc_info=True)

    def register(self, username: str, password: str) -> tuple[bool, str]:
        """Đăng ký tài khoản mới. Trả về (success, message)."""
        try:
            with Database() as db:
                existing = db.fetchone(
                    "SELECT id FROM users WHERE username = %s", (username,)
                )
                if existing:
                    return False, "Tên đăng nhập đã tồn tại."

                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, hashed),
                )
                return True, "Đăng ký thành công."
        except Exception as e:
            logger.error("auth.register failed: %s", e, exc_info=True)
            return False, f"Lỗi hệ thống: {e}"

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Đăng nhập. Trả về (success, message)."""
        try:
            with Database() as db:
                user = db.fetchone(
                    "SELECT id, username, password_hash, status FROM users "
                    "WHERE username = %s AND deleted_at IS NULL",
                    (username,),
                )
                if not user:
                    return False, "Tên đăng nhập không tồn tại."

                if user["status"] != "active":
                    return False, "Tài khoản đã bị khoá."

                if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                    return False, "Mật khẩu không đúng."

                db.execute(
                    "UPDATE users SET last_login_at = NOW() WHERE id = %s",
                    (user["id"],),
                )
                return True, user["username"]
        except Exception as e:
            logger.error("auth.login failed: %s", e, exc_info=True)
            return False, f"Lỗi hệ thống: {e}"


# Singleton
auth = AuthService()
