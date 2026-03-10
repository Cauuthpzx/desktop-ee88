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
	if _, err := db.Exec(migrateEmailToUsername); err != nil {
		return err
	}
	slog.Info("Migrations completed")
	return nil
}
