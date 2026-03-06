"""
server/routes/auth_routes.py — Dang ky, dang nhap.
"""
import logging

import bcrypt
from fastapi import APIRouter, Depends

from server.database import get_db
from server.auth import create_token
from server.models import RegisterReq, LoginReq, TokenResp, MsgResp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register", response_model=MsgResp)
def register(req: RegisterReq, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (req.username,))
    if cur.fetchone():
        return MsgResp(ok=False, message="server.username_exists")

    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (req.username, hashed),
    )
    logger.info("User registered: %s", req.username)
    return MsgResp(ok=True, message="server.register_success")


@router.post("/login", response_model=TokenResp)
def login(req: LoginReq, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT id, username, password_hash, role, status, token_version "
        "FROM users WHERE username = %s AND deleted_at IS NULL",
        (req.username,),
    )
    user = cur.fetchone()
    if not user:
        return TokenResp(ok=False, message="server.username_not_found")
    if user["status"] != "active":
        return TokenResp(ok=False, message="server.account_locked")
    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        return TokenResp(ok=False, message="server.wrong_login_password")

    cur.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user["id"],))
    token = create_token(user["id"], user["username"], user["role"], user["token_version"])
    logger.info("User logged in: %s", user["username"])
    return TokenResp(ok=True, token=token, username=user["username"], role=user["role"])
