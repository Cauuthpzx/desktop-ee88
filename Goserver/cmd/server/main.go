package main

import (
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"goserver/internal/config"
	"goserver/internal/database"
	"goserver/internal/handler"
	"goserver/internal/middleware"
	"goserver/internal/repository"
	"goserver/internal/service"
	"goserver/pkg/utils"
)

func setupLogger() *os.File {
	logDir := filepath.Join(".", "logs")
	os.MkdirAll(logDir, 0755)

	logFile := filepath.Join(logDir, time.Now().Format("2006-01-02")+".log")
	f, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		log.Printf("[WARN] Cannot open log file: %v, logging to console only", err)
		return nil
	}

	// Ghi cả console + file
	multi := io.MultiWriter(os.Stdout, f)
	log.SetOutput(multi)
	log.SetFlags(log.Ldate | log.Ltime | log.Lmicroseconds)

	return f
}

func main() {
	logFile := setupLogger()
	if logFile != nil {
		defer logFile.Close()
	}

	cfg := config.Load()

	// Database
	db, err := database.NewPostgres(cfg.DBConnString())
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	if err := database.Migrate(db); err != nil {
		log.Fatal("Failed to run migrations:", err)
	}

	// Layers
	userRepo := repository.NewUserRepository(db)
	authService := service.NewAuthService(userRepo, cfg)
	oauthService := service.NewOAuthService(userRepo, authService, cfg)

	authHandler := handler.NewAuthHandler(authService)
	oauthHandler := handler.NewOAuthHandler(oauthService, cfg)

	// Router
	mux := http.NewServeMux()

	// Rate limiters
	loginLimiter := middleware.NewRateLimiter(5, time.Minute)
	registerLimiter := middleware.NewRateLimiter(3, time.Minute)

	// Public routes
	mux.Handle("POST /api/auth/register",
		registerLimiter.Middleware(http.HandlerFunc(authHandler.Register)))
	mux.Handle("POST /api/auth/login",
		loginLimiter.Middleware(http.HandlerFunc(authHandler.Login)))

	// OAuth routes
	mux.HandleFunc("GET /api/auth/google", oauthHandler.GoogleLogin)
	mux.HandleFunc("GET /api/auth/google/callback", oauthHandler.GoogleCallback)
	mux.HandleFunc("GET /api/auth/facebook", oauthHandler.FacebookLogin)
	mux.HandleFunc("GET /api/auth/facebook/callback", oauthHandler.FacebookCallback)

	// Protected routes
	authMw := middleware.AuthMiddleware(authService)
	mux.Handle("POST /api/auth/change-password",
		authMw(http.HandlerFunc(authHandler.ChangePassword)))
	mux.Handle("POST /api/auth/logout",
		authMw(http.HandlerFunc(authHandler.Logout)))

	// Wrap with logging, CORS and error recovery
	finalHandler := middleware.RequestLogger(utils.CORS(utils.RecoverErrors(mux)))

	// Start server
	addr := ":" + cfg.ServerPort
	log.Printf("[SERVER] Starting on %s", addr)
	if err := http.ListenAndServe(addr, finalHandler); err != nil {
		log.Fatal("Server failed:", err)
	}
}
