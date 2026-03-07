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

CREATE TABLE IF NOT EXISTS agents (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    ext_username    VARCHAR(100) NOT NULL,
    ext_password    VARCHAR(500) NOT NULL DEFAULT '',
    base_url        VARCHAR(500),
    session_cookie  VARCHAR(500) DEFAULT '',
    cookie_expires  TIMESTAMPTZ,
    status          VARCHAR(20) DEFAULT 'offline',
    is_active       BOOLEAN DEFAULT TRUE,
    login_error     VARCHAR(500),
    login_attempts  INT DEFAULT 0,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, ext_username)
);

CREATE TABLE IF NOT EXISTS groups (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    description     VARCHAR(500) DEFAULT '',
    owner_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_members     INT DEFAULT 50,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS group_data_cache (
    id              BIGSERIAL PRIMARY KEY,
    group_id        BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    data_type       VARCHAR(50) NOT NULL,
    data_json       JSONB NOT NULL DEFAULT '[]',
    total_count     INT DEFAULT 0,
    agents_fetched  JSONB DEFAULT '[]',
    agents_errors   JSONB DEFAULT '[]',
    version         BIGINT DEFAULT 1,
    synced_by       BIGINT REFERENCES users(id),
    synced_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, data_type)
);

CREATE TABLE IF NOT EXISTS group_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    group_id        BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    action          VARCHAR(50) NOT NULL,
    target_agent_id BIGINT REFERENCES agents(id),
    details         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
"""

MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS presence VARCHAR(20) DEFAULT 'online'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(500) DEFAULT ''",
    # Group support — agents columns
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_key VARCHAR(12) UNIQUE",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS key_generated_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS group_id BIGINT REFERENCES groups(id)",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS group_joined_at TIMESTAMPTZ",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_view_data BOOLEAN DEFAULT TRUE",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_view_reports BOOLEAN DEFAULT TRUE",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_edit_data BOOLEAN DEFAULT FALSE",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_manage BOOLEAN DEFAULT FALSE",
    "ALTER TABLE agents ADD COLUMN IF NOT EXISTS grp_can_tools BOOLEAN DEFAULT TRUE",
    # Indexes
    "CREATE INDEX IF NOT EXISTS idx_gdc_group ON group_data_cache(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_agents_group ON agents(group_id)",
    "CREATE INDEX IF NOT EXISTS idx_gal_group ON group_audit_log(group_id)",
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
