"""
MaxHub API Server — FastAPI backend for desktop app.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

import jwt
import bcrypt
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────
DB_DSN = (
    f"host={os.getenv('DB_HOST', 'localhost')} "
    f"port={os.getenv('DB_PORT', '5432')} "
    f"dbname={os.getenv('DB_NAME', 'maxhub')} "
    f"user={os.getenv('DB_USER', 'postgres')} "
    f"password={os.getenv('DB_PASSWORD', '')}"
)
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_EXPIRE = int(os.getenv("JWT_EXPIRE_HOURS", "72"))


# ── Database ────────────────────────────────────────────────
def get_db():
    conn = psycopg.connect(DB_DSN, row_factory=dict_row, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
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
"""

MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS presence VARCHAR(20) DEFAULT 'online'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(500) DEFAULT ''",
]


# ── Lifespan ────────────────────────────────────────────────
def _init_schema() -> None:
    """Run once before workers start."""
    conn = psycopg.connect(DB_DSN, autocommit=True)
    conn.execute(SCHEMA)
    for sql in MIGRATIONS:
        try:
            conn.execute(sql)
        except Exception as e:
            logger.debug("Migration skipped: %s", e)
    conn.close()
    logger.info("Database schema ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MaxHub API started.")
    yield
    logger.info("Shutting down.")


app = FastAPI(title="MaxHub API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── JWT helpers ─────────────────────────────────────────────
def create_token(user_id: int, username: str, role: str, token_version: int) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "tv": token_version,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token het han.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token khong hop le.")


def get_current_user(authorization: str = Header(...), db=Depends(get_db)) -> dict:
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


# ── Models ──────────────────────────────────────────────────
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


# ── Auth endpoints ──────────────────────────────────────────
@app.post("/api/register", response_model=MsgResp)
def register(req: RegisterReq, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (req.username,))
    if cur.fetchone():
        return MsgResp(ok=False, message="Ten dang nhap da ton tai.")

    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (req.username, hashed),
    )
    logger.info("User registered: %s", req.username)
    return MsgResp(ok=True, message="Dang ky thanh cong.")


@app.post("/api/login", response_model=TokenResp)
def login(req: LoginReq, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT id, username, password_hash, role, status, token_version "
        "FROM users WHERE username = %s AND deleted_at IS NULL",
        (req.username,),
    )
    user = cur.fetchone()
    if not user:
        return TokenResp(ok=False, message="Ten dang nhap khong ton tai.")
    if user["status"] != "active":
        return TokenResp(ok=False, message="Tai khoan da bi khoa.")
    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        return TokenResp(ok=False, message="Mat khau khong dung.")

    cur.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user["id"],))
    token = create_token(user["id"], user["username"], user["role"], user["token_version"])
    logger.info("User logged in: %s", user["username"])
    return TokenResp(ok=True, token=token, username=user["username"], role=user["role"])


@app.get("/api/me", response_model=ProfileResp)
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


@app.put("/api/me", response_model=MsgResp)
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
        return MsgResp(ok=True, message="Khong co thay doi.")
    fields.append("updated_at = NOW()")
    values.append(user["id"])
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
    cur.execute(sql, tuple(values))
    logger.info("User %s updated profile.", user["username"])
    return MsgResp(ok=True, message="Cap nhat thanh cong.")


@app.put("/api/me/password", response_model=MsgResp)
def change_password(req: ChangePasswordReq, user=Depends(get_current_user), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id = %s", (user["id"],))
    row = cur.fetchone()
    if not bcrypt.checkpw(req.current_password.encode(), row["password_hash"].encode()):
        return MsgResp(ok=False, message="Mat khau hien tai khong dung.")
    new_hash = bcrypt.hashpw(req.new_password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        "UPDATE users SET password_hash = %s, token_version = token_version + 1, updated_at = NOW() "
        "WHERE id = %s",
        (new_hash, user["id"]),
    )
    logger.info("User %s changed password.", user["username"])
    return MsgResp(ok=True, message="Doi mat khau thanh cong.")


@app.get("/api/health")
def health():
    return {"ok": True, "service": "maxhub-api"}


# ── Version / Update ────────────────────────────────────────
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
UPDATE_URL = os.getenv("UPDATE_URL", "")  # URL to .exe file


@app.get("/api/version")
def version():
    return {
        "version": APP_VERSION,
        "update_url": UPDATE_URL,
        "force": False,
    }


if __name__ == "__main__":
    _init_schema()
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
