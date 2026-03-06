"""
server/config.py — Cau hinh ung dung doc tu .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "maxhub")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DB_DSN = (
    f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} "
    f"user={DB_USER} password={DB_PASSWORD}"
)

# ── JWT ───────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "72"))

# ── App version / Update ─────────────────────────────────────
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
UPDATE_URL = os.getenv("UPDATE_URL", "")
UPDATE_SHA256 = os.getenv("UPDATE_SHA256", "")
UPDATE_CHANGELOG = os.getenv("UPDATE_CHANGELOG", "")
UPDATE_FORCE = os.getenv("UPDATE_FORCE", "false").lower() == "true"
UPDATE_FILE_SIZE = int(os.getenv("UPDATE_FILE_SIZE", "0"))

# ── Upstream (EE88) ──────────────────────────────────────────
UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "https://a2u4k.ee88dly.com")
