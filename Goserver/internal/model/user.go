package model

import "time"

type User struct {
	ID        int64     `json:"id" db:"id"`
	Username  string    `json:"username" db:"username"`
	Password  string    `json:"-" db:"password"`
	Settings  *string   `json:"settings,omitempty" db:"settings"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	LastSeen  time.Time `json:"last_seen" db:"last_seen"`
}

type Session struct {
	Cookie   string    `db:"cookie"`
	UserID   int64     `db:"user_id"`
	LastUsed time.Time `db:"last_used"`
}

type OAuth struct {
	Method    string `db:"method"`
	ForeignID string `db:"foreign_id"`
	Token     string `db:"token"`
	UserID    int64  `db:"user_id"`
}

// Request/Response DTOs

type RegisterRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type ChangePasswordRequest struct {
	OldPassword string `json:"old_password"`
	NewPassword string `json:"new_password"`
}

type AuthResponse struct {
	Status string    `json:"status"`
	Data   *AuthData `json:"data,omitempty"`
	Message string   `json:"message,omitempty"`
}

type AuthData struct {
	User  *UserResponse `json:"user"`
	Token string        `json:"token"`
}

type UserResponse struct {
	ID        int64     `json:"id"`
	Username  string    `json:"username"`
	CreatedAt time.Time `json:"created_at"`
}

func (u *User) ToResponse() *UserResponse {
	return &UserResponse{
		ID:        u.ID,
		Username:  u.Username,
		CreatedAt: u.CreatedAt,
	}
}
