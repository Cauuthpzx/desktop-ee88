"""
server/models.py — Pydantic request/response models.
"""
from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────
class RegisterReq(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=255)


class LoginReq(BaseModel):
    username: str
    password: str


class TokenResp(BaseModel):
    ok: bool
    token: str | None = None
    username: str | None = None
    role: str | None = None
    message: str | None = None


class MsgResp(BaseModel):
    ok: bool
    message: str


# ── Profile ───────────────────────────────────────────────────
class ProfileResp(BaseModel):
    ok: bool
    username: str | None = None
    email: str | None = None
    role: str | None = None
    presence: str | None = None
    bio: str | None = None
    created_at: str | None = None
    last_login_at: str | None = None
    message: str | None = None


class UpdateProfileReq(BaseModel):
    email: str | None = Field(None, max_length=255)
    presence: str | None = Field(None, pattern="^(online|busy|away|dnd|invisible)$")
    bio: str | None = Field(None, max_length=500)


class ChangePasswordReq(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=255)
