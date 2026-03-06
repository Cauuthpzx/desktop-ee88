"""
server/auth.py — JWT helpers va get_current_user dependency.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Depends, Header

from server.config import JWT_SECRET, JWT_EXPIRE_HOURS
from server.database import get_db


def create_token(user_id: int, username: str, role: str, token_version: int) -> str:
    """Tao JWT token."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "tv": token_version,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Giai ma JWT token. Raise HTTPException neu loi."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token het han.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token khong hop le.")


def get_current_user(authorization: str = Header(...), db=Depends(get_db)) -> dict:
    """FastAPI dependency: xac thuc user tu Bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token.")
    token = authorization[7:]
    payload = decode_token(token)

    cur = db.cursor()
    cur.execute(
        "SELECT id, username, role, status, token_version "
        "FROM users WHERE id = %s AND deleted_at IS NULL",
        (int(payload["sub"]),),
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(401, "User not found.")
    if user["status"] != "active":
        raise HTTPException(403, "Tai khoan bi khoa.")
    if user["token_version"] != payload.get("tv", 0):
        raise HTTPException(401, "Token da bi thu hoi.")
    return user
