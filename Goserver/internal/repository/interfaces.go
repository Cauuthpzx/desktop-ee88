package repository

import (
	"context"
	"time"

	"goserver/internal/model"
)

// UserRepo định nghĩa contract cho user data access.
// Service layer chỉ biết interface này, không biết implementation.
type UserRepo interface {
	Create(ctx context.Context, username, hashedPassword string) (*model.User, error)
	FindByUsername(ctx context.Context, username string) (*model.User, error)
	FindByID(ctx context.Context, id int64) (*model.User, error)
	UpdatePassword(ctx context.Context, userID int64, hashedPassword string) error
	UpdateLastSeen(ctx context.Context, userID int64) error

	CreateSession(ctx context.Context, cookie string, userID int64) error
	FindSession(ctx context.Context, cookie string) (*model.Session, error)
	DeleteSession(ctx context.Context, cookie string) error
	DeleteUserSessions(ctx context.Context, userID int64) error
	CleanExpiredSessions(ctx context.Context, expiry time.Duration) error

	FindOAuth(ctx context.Context, method, foreignID string) (*model.OAuth, error)
	CreateOAuth(ctx context.Context, oauth *model.OAuth) error
}
