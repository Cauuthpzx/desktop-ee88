"""
server/routes/user_routes.py — Profile, doi mat khau.
"""
import logging

import bcrypt
from fastapi import APIRouter, Depends

from server.database import get_db
from server.auth import get_current_user
from server.models import (
    ProfileResp, UpdateProfileReq, ChangePasswordReq, MsgResp,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["user"])


@router.get("/me", response_model=ProfileResp)
def me(user=Depends(get_current_user), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT username, email, role, presence, bio, created_at, last_login_at "
        "FROM users WHERE id = %s",
        (user["id"],),
    )
    row = cur.fetchone()
    return ProfileResp(
        ok=True,
        username=row["username"],
        email=row["email"] or "",
        role=row["role"],
        presence=row.get("presence", "online"),
        bio=row.get("bio", ""),
        created_at=str(row["created_at"]) if row["created_at"] else None,
        last_login_at=str(row["last_login_at"]) if row["last_login_at"] else None,
    )


@router.put("/me", response_model=MsgResp)
def update_profile(req: UpdateProfileReq, user=Depends(get_current_user), db=Depends(get_db)):
    cur = db.cursor()
    fields = []
    values = []
    if req.email is not None:
        fields.append("email = %s")
        values.append(req.email)
    if req.presence is not None:
        fields.append("presence = %s")
        values.append(req.presence)
    if req.bio is not None:
        fields.append("bio = %s")
        values.append(req.bio)
    if not fields:
        return MsgResp(ok=True, message="server.no_changes")
    fields.append("updated_at = NOW()")
    values.append(user["id"])
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
    cur.execute(sql, tuple(values))
    logger.info("User %s updated profile.", user["username"])
    return MsgResp(ok=True, message="server.update_success")


@router.put("/me/password", response_model=MsgResp)
def change_password(req: ChangePasswordReq, user=Depends(get_current_user), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id = %s", (user["id"],))
    row = cur.fetchone()
    if not bcrypt.checkpw(req.current_password.encode(), row["password_hash"].encode()):
        return MsgResp(ok=False, message="server.wrong_password")
    new_hash = bcrypt.hashpw(req.new_password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        "UPDATE users SET password_hash = %s, token_version = token_version + 1, updated_at = NOW() "
        "WHERE id = %s",
        (new_hash, user["id"]),
    )
    logger.info("User %s changed password.", user["username"])
    return MsgResp(ok=True, message="server.password_changed")
