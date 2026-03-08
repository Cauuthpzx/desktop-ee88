"""
Test data factories — tạo dữ liệu test nhanh.
"""
from __future__ import annotations
from datetime import datetime, timezone


def make_user(
    id: int = 1,
    username: str = "testuser",
    role: str = "user",
    status: str = "active",
    token_version: int = 0,
    **kwargs,
) -> dict:
    """Tạo user dict giả cho tests."""
    return {
        "id": id,
        "username": username,
        "role": role,
        "status": status,
        "token_version": token_version,
        "email": kwargs.get("email", f"{username}@test.com"),
        "presence": kwargs.get("presence", "online"),
        "bio": kwargs.get("bio", ""),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
        "last_login_at": kwargs.get("last_login_at"),
        "deleted_at": None,
    }


def make_agent(
    id: int = 1,
    user_id: int = 1,
    name: str = "Test Agent",
    ext_username: str = "ext_user",
    **kwargs,
) -> dict:
    """Tạo agent dict giả cho tests."""
    return {
        "id": id,
        "user_id": user_id,
        "name": name,
        "ext_username": ext_username,
        "ext_password": kwargs.get("ext_password", ""),
        "base_url": kwargs.get("base_url", "https://example.com"),
        "session_cookie": kwargs.get("session_cookie", ""),
        "status": kwargs.get("status", "offline"),
        "is_active": kwargs.get("is_active", True),
        "group_id": kwargs.get("group_id"),
        "agent_key": kwargs.get("agent_key"),
    }


def make_group(
    id: int = 1,
    name: str = "Test Group",
    owner_id: int = 1,
    **kwargs,
) -> dict:
    """Tạo group dict giả cho tests."""
    return {
        "id": id,
        "name": name,
        "description": kwargs.get("description", ""),
        "owner_id": owner_id,
        "max_members": kwargs.get("max_members", 50),
        "is_active": kwargs.get("is_active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
        "updated_at": kwargs.get("updated_at", datetime.now(timezone.utc)),
        "deleted_at": None,
    }
