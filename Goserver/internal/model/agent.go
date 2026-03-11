package model

import (
	"database/sql"
	"time"
)

// Agent đại diện cho 1 tài khoản đại lý EE88 upstream.
type Agent struct {
	ID            int64          `json:"id" db:"id"`
	Name          string         `json:"name" db:"name"`
	ExtUsername   string         `json:"ext_username" db:"ext_username"`
	ExtPassword      string         `json:"-" db:"ext_password"`
	BaseURL          sql.NullString `json:"base_url" db:"base_url"`
	SessionCookie    string         `json:"-" db:"session_cookie"`
	EncryptPublicKey string         `json:"-" db:"encrypt_public_key"` // EE88 AES encrypt mode key
	CookieExpires sql.NullTime   `json:"cookie_expires" db:"cookie_expires"`
	Status        string         `json:"status" db:"status"` // active, offline, logging_in, error
	IsActive      bool           `json:"is_active" db:"is_active"`
	LoginError    sql.NullString `json:"login_error" db:"login_error"`
	LoginAttempts int            `json:"login_attempts" db:"login_attempts"`
	LastLoginAt   sql.NullTime   `json:"last_login_at" db:"last_login_at"`
	AutoLogin     bool           `json:"auto_login" db:"auto_login"`
	CreatedAt     time.Time      `json:"created_at" db:"created_at"`
	UpdatedAt     time.Time      `json:"updated_at" db:"updated_at"`
}

// AgentSafe là response an toàn — không leak password/cookie.
type AgentSafe struct {
	ID            int64      `json:"id"`
	Name          string     `json:"name"`
	ExtUsername   string     `json:"ext_username"`
	BaseURL       string     `json:"base_url,omitempty"`
	Status        string     `json:"status"`
	IsActive      bool       `json:"is_active"`
	CookieExpires *time.Time `json:"cookie_expires,omitempty"`
	LastLoginAt   *time.Time `json:"last_login_at,omitempty"`
	LoginError    string     `json:"login_error,omitempty"`
	LoginAttempts int        `json:"login_attempts"`
	AutoLogin     bool       `json:"auto_login"`
	CreatedAt     time.Time  `json:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at"`
}

func (a *Agent) ToSafe() *AgentSafe {
	s := &AgentSafe{
		ID:            a.ID,
		Name:          a.Name,
		ExtUsername:   a.ExtUsername,
		Status:        a.Status,
		IsActive:      a.IsActive,
		LoginAttempts: a.LoginAttempts,
		AutoLogin:     a.AutoLogin,
		CreatedAt:     a.CreatedAt,
		UpdatedAt:     a.UpdatedAt,
	}
	if a.BaseURL.Valid {
		s.BaseURL = a.BaseURL.String
	}
	if a.CookieExpires.Valid {
		s.CookieExpires = &a.CookieExpires.Time
	}
	if a.LastLoginAt.Valid {
		s.LastLoginAt = &a.LastLoginAt.Time
	}
	if a.LoginError.Valid {
		s.LoginError = a.LoginError.String
	}
	return s
}

// AgentLoginHistory ghi lại lịch sử đăng nhập.
type AgentLoginHistory struct {
	ID              int64          `json:"id" db:"id"`
	AgentID         int64          `json:"agent_id" db:"agent_id"`
	Success         bool           `json:"success" db:"success"`
	CaptchaAttempts int            `json:"captcha_attempts" db:"captcha_attempts"`
	ErrorMessage    sql.NullString `json:"error_message" db:"error_message"`
	IPAddress       sql.NullString `json:"ip_address" db:"ip_address"`
	TriggeredBy     string         `json:"triggered_by" db:"triggered_by"` // manual, auto-relogin, scheduler
	CreatedAt       time.Time      `json:"created_at" db:"created_at"`
}

// Request DTOs

type CreateAgentRequest struct {
	Name        string `json:"name"`
	ExtUsername string `json:"ext_username"`
	ExtPassword string `json:"ext_password"`
	BaseURL     string `json:"base_url,omitempty"`
}

type UpdateAgentRequest struct {
	Name        *string `json:"name,omitempty"`
	ExtPassword *string `json:"ext_password,omitempty"`
	BaseURL     *string `json:"base_url,omitempty"`
	IsActive    *bool   `json:"is_active,omitempty"`
	AutoLogin   *bool   `json:"auto_login,omitempty"`
}

type SetCookieRequest struct {
	Cookie string `json:"cookie"`
}

// Login result
type LoginResult struct {
	Success         bool   `json:"success"`
	CaptchaAttempts int    `json:"captcha_attempts"`
	ErrorMessage    string `json:"error_message,omitempty"`
}

type SessionInfo struct {
	ID            int64      `json:"id"`
	Name          string     `json:"name"`
	Status        string     `json:"status"`
	HasSession    bool       `json:"has_session"`
	CookieExpires *time.Time `json:"cookie_expires,omitempty"`
	LastLoginAt   *time.Time `json:"last_login_at,omitempty"`
	LoginError    string     `json:"login_error,omitempty"`
}

type LoginAllResult struct {
	Total   int `json:"total"`
	Success int `json:"success"`
	Failed  int `json:"failed"`
}

type CookieHealthResult struct {
	ID    int64  `json:"id"`
	Name  string `json:"name"`
	Alive bool   `json:"alive"`
}

// AgentUpstreamInfo — thông tin cần để Desktop fetch trực tiếp upstream.
type AgentUpstreamInfo struct {
	ID               int64  `json:"id"`
	Name             string `json:"name"`
	BaseURL          string `json:"base_url"`
	Cookie           string `json:"cookie"`
	EncryptPublicKey string `json:"encrypt_public_key"`
}

func (a *Agent) ToUpstreamInfo() *AgentUpstreamInfo {
	info := &AgentUpstreamInfo{
		ID:               a.ID,
		Name:             a.Name,
		Cookie:           a.SessionCookie,
		EncryptPublicKey: a.EncryptPublicKey,
	}
	if a.BaseURL.Valid {
		info.BaseURL = a.BaseURL.String
	}
	return info
}
