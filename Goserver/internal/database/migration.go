package database

import (
	"log/slog"

	"github.com/jmoiron/sqlx"
)

const schema = `
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT,
    settings TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    cookie TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_used TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS oauth (
    method TEXT NOT NULL,
    foreign_id TEXT NOT NULL,
    token TEXT,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(method, foreign_id)
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token TEXT NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expiry TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    ext_username TEXT NOT NULL UNIQUE,
    ext_password TEXT NOT NULL DEFAULT '',
    base_url TEXT,
    session_cookie TEXT NOT NULL DEFAULT '',
    cookie_expires TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'offline',
    is_active BOOLEAN NOT NULL DEFAULT true,
    login_error TEXT,
    login_attempts INTEGER NOT NULL DEFAULT 0,
    last_login_at TIMESTAMP,
    auto_login BOOLEAN NOT NULL DEFAULT false,
    encrypt_public_key TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_login_history (
    id BIGSERIAL PRIMARY KEY,
    agent_id BIGINT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    success BOOLEAN NOT NULL DEFAULT false,
    captcha_attempts INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    ip_address TEXT,
    triggered_by TEXT NOT NULL DEFAULT 'manual',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_login_history_agent_id ON agent_login_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON agents(is_active);
`

const migrateAddEncryptKey = `
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'agents' AND column_name = 'encrypt_public_key'
    ) THEN
        ALTER TABLE agents ADD COLUMN encrypt_public_key TEXT NOT NULL DEFAULT '';
    ELSE
        UPDATE agents SET encrypt_public_key = '' WHERE encrypt_public_key IS NULL;
        ALTER TABLE agents ALTER COLUMN encrypt_public_key SET NOT NULL;
        ALTER TABLE agents ALTER COLUMN encrypt_public_key SET DEFAULT '';
    END IF;
END $$;
`

const migrateEmailToUsername = `
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'email'
    ) THEN
        ALTER TABLE users RENAME COLUMN email TO username;
    END IF;
END $$;
`

func Migrate(db *sqlx.DB) error {
	slog.Info("Running database migrations...")
	if _, err := db.Exec(schema); err != nil {
		return err
	}
	if _, err := db.Exec(migrateAddEncryptKey); err != nil {
		return err
	}
	if _, err := db.Exec(migrateEmailToUsername); err != nil {
		return err
	}
	slog.Info("Migrations completed")
	return nil
}
