"""
server/database.py — Ket noi PostgreSQL, schema, migrations.
"""
import logging

import psycopg
from psycopg.rows import dict_row

from server.config import DB_DSN

logger = logging.getLogger(__name__)

# ── Dependency — dung voi Depends(get_db) ─────────────────────
def get_db():
    """FastAPI dependency: mo connection, tra ve, dong khi xong."""
    conn = psycopg.connect(DB_DSN, row_factory=dict_row, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


# ── Schema ────────────────────────────────────────────────────
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


def init_schema() -> None:
    """Chay schema + migrations. Goi truoc khi start workers."""
    conn = psycopg.connect(DB_DSN, autocommit=True)
    conn.execute(SCHEMA)
    for sql in MIGRATIONS:
        try:
            conn.execute(sql)
        except Exception as e:
            logger.debug("Migration skipped: %s", e)
    conn.close()
    logger.info("Database schema ready.")
