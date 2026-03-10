package repository

import (
	"context"
	"database/sql"
	"errors"
	"time"

	"github.com/jmoiron/sqlx"

	"goserver/internal/model"
)

var (
	ErrUserNotFound    = errors.New("user not found")
	ErrUsernameExists  = errors.New("username already exists")
)

type UserRepository struct {
	db *sqlx.DB
}

func NewUserRepository(db *sqlx.DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) Create(ctx context.Context, username, hashedPassword string) (*model.User, error) {
	var user model.User
	err := r.db.QueryRowxContext(ctx,
		`INSERT INTO users (username, password, created_at, last_seen)
		 VALUES ($1, $2, NOW(), NOW())
		 RETURNING id, username, password, settings, created_at, last_seen`,
		username, hashedPassword,
	).StructScan(&user)

	if err != nil {
		if isUniqueViolation(err) {
			return nil, ErrUsernameExists
		}
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) FindByUsername(ctx context.Context, username string) (*model.User, error) {
	var user model.User
	err := r.db.GetContext(ctx, &user,
		`SELECT id, username, password, settings, created_at, last_seen FROM users WHERE username = $1`, username)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrUserNotFound
	}
	return &user, err
}

func (r *UserRepository) FindByID(ctx context.Context, id int64) (*model.User, error) {
	var user model.User
	err := r.db.GetContext(ctx, &user,
		`SELECT id, username, password, settings, created_at, last_seen FROM users WHERE id = $1`, id)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrUserNotFound
	}
	return &user, err
}

func (r *UserRepository) UpdatePassword(ctx context.Context, userID int64, hashedPassword string) error {
	_, err := r.db.ExecContext(ctx,
		`UPDATE users SET password = $1 WHERE id = $2`, hashedPassword, userID)
	return err
}

func (r *UserRepository) UpdateLastSeen(ctx context.Context, userID int64) error {
	_, err := r.db.ExecContext(ctx,
		`UPDATE users SET last_seen = NOW() WHERE id = $1`, userID)
	return err
}

// Session methods

func (r *UserRepository) CreateSession(ctx context.Context, cookie string, userID int64) error {
	_, err := r.db.ExecContext(ctx,
		`INSERT INTO sessions (cookie, user_id, last_used) VALUES ($1, $2, NOW())`,
		cookie, userID)
	return err
}

func (r *UserRepository) FindSession(ctx context.Context, cookie string) (*model.Session, error) {
	var session model.Session
	err := r.db.GetContext(ctx, &session,
		`SELECT cookie, user_id, last_used FROM sessions WHERE cookie = $1`, cookie)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	return &session, err
}

func (r *UserRepository) DeleteSession(ctx context.Context, cookie string) error {
	_, err := r.db.ExecContext(ctx,
		`DELETE FROM sessions WHERE cookie = $1`, cookie)
	return err
}

func (r *UserRepository) DeleteUserSessions(ctx context.Context, userID int64) error {
	_, err := r.db.ExecContext(ctx,
		`DELETE FROM sessions WHERE user_id = $1`, userID)
	return err
}

func (r *UserRepository) CleanExpiredSessions(ctx context.Context, expiry time.Duration) error {
	_, err := r.db.ExecContext(ctx,
		`DELETE FROM sessions WHERE last_used < $1`, time.Now().Add(-expiry))
	return err
}

// OAuth methods

func (r *UserRepository) FindOAuth(ctx context.Context, method, foreignID string) (*model.OAuth, error) {
	var oauth model.OAuth
	err := r.db.GetContext(ctx, &oauth,
		`SELECT method, foreign_id, token, user_id FROM oauth WHERE method = $1 AND foreign_id = $2`,
		method, foreignID)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	return &oauth, err
}

func (r *UserRepository) CreateOAuth(ctx context.Context, oauth *model.OAuth) error {
	_, err := r.db.ExecContext(ctx,
		`INSERT INTO oauth (method, foreign_id, token, user_id) VALUES ($1, $2, $3, $4)`,
		oauth.Method, oauth.ForeignID, oauth.Token, oauth.UserID)
	return err
}

func isUniqueViolation(err error) bool {
	return err != nil && (contains(err.Error(), "unique") || contains(err.Error(), "duplicate"))
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && searchString(s, substr)
}

func searchString(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
