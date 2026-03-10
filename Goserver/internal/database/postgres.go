package database

import (
	"fmt"
	"log"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
)

func NewPostgres(connStr string) (*sqlx.DB, error) {
	log.Println("[DB] Connecting to PostgreSQL...")
	db, err := sqlx.Connect("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)

	log.Println("[DB] Connected (max_open=25, max_idle=5)")
	return db, nil
}
