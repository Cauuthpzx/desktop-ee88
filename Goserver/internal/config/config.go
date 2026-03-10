package config

import (
	"fmt"
	"log/slog"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	ServerPort   string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration

	DBHost     string
	DBPort     string
	DBUser     string
	DBPassword string
	DBName     string

	JWTSecret     string
	JWTExpiry     time.Duration
	SessionExpiry time.Duration

	GoogleClientID     string
	GoogleClientSecret string
	GoogleRedirectURL  string

	FacebookClientID     string
	FacebookClientSecret string
	FacebookRedirectURL  string

	FrontendURL    string
	AllowedOrigins []string
}

func Load() *Config {
	return &Config{
		ServerPort:   getEnv("SERVER_PORT", "8080"),
		ReadTimeout:  parseDuration(getEnv("READ_TIMEOUT", "5s")),
		WriteTimeout: parseDuration(getEnv("WRITE_TIMEOUT", "10s")),
		IdleTimeout:  parseDuration(getEnv("IDLE_TIMEOUT", "60s")),

		DBHost:     getEnv("DB_HOST", "localhost"),
		DBPort:     getEnv("DB_PORT", "5432"),
		DBUser:     getEnv("DB_USER", "postgres"),
		DBPassword: getEnv("DB_PASSWORD", "secret"),
		DBName:     getEnv("DB_NAME", "goserver"),

		JWTSecret:     getEnv("JWT_SECRET", "dev-secret-change-in-production"),
		JWTExpiry:     parseDuration(getEnv("JWT_EXPIRY", "24h")),
		SessionExpiry: parseDuration(getEnv("SESSION_EXPIRY", "168h")),

		GoogleClientID:     getEnv("GOOGLE_CLIENT_ID", ""),
		GoogleClientSecret: getEnv("GOOGLE_CLIENT_SECRET", ""),
		GoogleRedirectURL:  getEnv("GOOGLE_REDIRECT_URL", "http://localhost:8080/api/auth/google/callback"),

		FacebookClientID:     getEnv("FACEBOOK_CLIENT_ID", ""),
		FacebookClientSecret: getEnv("FACEBOOK_CLIENT_SECRET", ""),
		FacebookRedirectURL:  getEnv("FACEBOOK_REDIRECT_URL", "http://localhost:8080/api/auth/facebook/callback"),

		FrontendURL:    getEnv("FRONTEND_URL", "http://localhost:3000"),
		AllowedOrigins: parseOrigins(getEnv("ALLOWED_ORIGINS", "http://localhost:3000")),
	}
}

func (c *Config) Validate() error {
	port, err := strconv.Atoi(c.ServerPort)
	if err != nil || port < 1 || port > 65535 {
		return fmt.Errorf("SERVER_PORT phải trong range 1-65535, got: %s", c.ServerPort)
	}
	if c.JWTSecret == "" {
		return fmt.Errorf("JWT_SECRET phải được set")
	}
	if c.JWTSecret == "dev-secret-change-in-production" {
		slog.Warn("JWT_SECRET đang dùng default — chỉ dùng cho development!")
	}
	if c.DBHost == "" || c.DBName == "" || c.DBUser == "" {
		return fmt.Errorf("DB_HOST, DB_NAME, DB_USER không được trống")
	}
	if c.DBPassword == "" {
		return fmt.Errorf("DB_PASSWORD phải được set")
	}
	if c.JWTExpiry <= 0 {
		return fmt.Errorf("JWT_EXPIRY phải dương")
	}
	if c.SessionExpiry <= 0 {
		return fmt.Errorf("SESSION_EXPIRY phải dương")
	}
	return nil
}

func (c *Config) DBConnString() string {
	return "host=" + c.DBHost +
		" port=" + c.DBPort +
		" user=" + c.DBUser +
		" password=" + c.DBPassword +
		" dbname=" + c.DBName +
		" sslmode=disable"
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func parseDuration(s string) time.Duration {
	d, err := time.ParseDuration(s)
	if err != nil {
		return 24 * time.Hour
	}
	return d
}

func parseOrigins(s string) []string {
	parts := strings.Split(s, ",")
	origins := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			origins = append(origins, p)
		}
	}
	return origins
}
