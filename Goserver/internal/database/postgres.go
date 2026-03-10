package database

import (
	"fmt"
	"log/slog"
	"time"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

func NewPostgres(connStr string) (*sqlx.DB, error) {
	slog.Info("Connecting to PostgreSQL...")
	db, err := sqlx.Connect("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(10)
	db.SetConnMaxLifetime(5 * time.Minute)
	db.SetConnMaxIdleTime(1 * time.Minute)

	slog.Info("Database connected",
		"max_open", 25,
		"max_idle", 10,
		"max_lifetime", "5m",
		"max_idle_time", "1m",
	)
	return db, nil
}
