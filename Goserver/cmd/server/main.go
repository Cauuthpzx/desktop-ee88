package main

import (
	"context"
	"io"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"goserver/internal/config"
	"goserver/internal/database"
	"goserver/internal/handler"
	"goserver/internal/middleware"
	"goserver/internal/repository"
	"goserver/internal/service"
	"goserver/pkg/utils"

	"github.com/joho/godotenv"
)

func setupLogger() *os.File {
	logDir := filepath.Join(".", "logs")
	os.MkdirAll(logDir, 0755)

	logFile := filepath.Join(logDir, time.Now().Format("2006-01-02")+".log")
	f, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})))
		slog.Warn("Cannot open log file, logging to console only", "error", err)
		return nil
	}

	multi := io.MultiWriter(os.Stdout, f)
	slog.SetDefault(slog.New(slog.NewJSONHandler(multi, &slog.HandlerOptions{Level: slog.LevelInfo})))
	return f
}

func main() {
	// Load .env file (nếu có)
	_ = godotenv.Load()

	logFile := setupLogger()
	if logFile != nil {
		defer logFile.Close()
	}

	// Config
	cfg := config.Load()
	if err := cfg.Validate(); err != nil {
		slog.Error("Invalid config", "error", err)
		os.Exit(1)
	}

	// Database
	db, err := database.NewPostgres(cfg.DBConnString())
	if err != nil {
		slog.Error("Failed to connect to database", "error", err)
		os.Exit(1)
	}
	defer db.Close()

	if err := database.Migrate(db); err != nil {
		slog.Error("Failed to run migrations", "error", err)
		os.Exit(1)
	}

	// Layers — Auth
	userRepo := repository.NewUserRepository(db)
	authService := service.NewAuthService(userRepo, cfg)
	oauthService := service.NewOAuthService(userRepo, authService, cfg)

	authHandler := handler.NewAuthHandler(authService)
	oauthHandler := handler.NewOAuthHandler(oauthService, cfg)
	healthHandler := handler.NewHealthHandler(db)

	// Layers — Agent / EE88
	agentRepo := repository.NewAgentRepository(db)

	// Load agent cache từ DB → 0ms lookup thay vì 1-3ms query
	agentCache := service.GetAgentCache()
	if err := agentCache.LoadFromDB(context.Background(), agentRepo); err != nil {
		slog.Warn("Failed to load agent cache", "error", err)
	}

	agentService := service.NewAgentService(agentRepo)
	loginService := service.NewEE88LoginService(agentRepo)
	agentHandler := handler.NewAgentHandler(agentService, loginService)

	// Layers — Customer (upstream proxy)
	customerService := service.NewCustomerService()
	customerHandler := handler.NewCustomerHandler(customerService)

	// Router
	mux := http.NewServeMux()

	// Rate limiters
	loginLimiter := middleware.NewRateLimiter(5, time.Minute)
	registerLimiter := middleware.NewRateLimiter(3, time.Minute)

	// Health (không qua auth/rate limit)
	mux.HandleFunc("GET /health/live", healthHandler.Live)
	mux.HandleFunc("GET /health/ready", healthHandler.Ready)

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

	// Agent CRUD routes (protected)
	mux.Handle("GET /api/agents", authMw(http.HandlerFunc(agentHandler.ListAgents)))
	mux.Handle("GET /api/agents/cookie-health", authMw(http.HandlerFunc(agentHandler.CookieHealth)))
	mux.Handle("GET /api/agents/{id}", authMw(http.HandlerFunc(agentHandler.GetAgent)))
	mux.Handle("POST /api/agents", authMw(http.HandlerFunc(agentHandler.CreateAgent)))
	mux.Handle("PATCH /api/agents/{id}", authMw(http.HandlerFunc(agentHandler.UpdateAgent)))
	mux.Handle("DELETE /api/agents/{id}", authMw(http.HandlerFunc(agentHandler.DeleteAgent)))

	// EE88 Auth routes (protected)
	mux.Handle("POST /api/ee88-auth/{id}/login", authMw(http.HandlerFunc(agentHandler.LoginAgent)))
	mux.Handle("POST /api/ee88-auth/{id}/logout", authMw(http.HandlerFunc(agentHandler.LogoutAgent)))
	mux.Handle("POST /api/ee88-auth/login-all", authMw(http.HandlerFunc(agentHandler.LoginAllAgents)))
	mux.Handle("POST /api/ee88-auth/{id}/check", authMw(http.HandlerFunc(agentHandler.CheckAgentSession)))
	mux.Handle("GET /api/ee88-auth/{id}/session", authMw(http.HandlerFunc(agentHandler.GetSessionInfo)))
	mux.Handle("PATCH /api/ee88-auth/{id}/cookie", authMw(http.HandlerFunc(agentHandler.SetCookieManual)))
	mux.Handle("GET /api/ee88-auth/{id}/login-history", authMw(http.HandlerFunc(agentHandler.GetLoginHistory)))

	// Customer upstream proxy (protected)
	mux.Handle("GET /api/customers", authMw(http.HandlerFunc(customerHandler.ListCustomers)))

	// Scheduler — health check + auto-login
	scheduler := service.NewScheduler(loginService, agentRepo)
	scheduler.Start()
	defer scheduler.Stop()

	// Shutdown captcha solver khi exit
	defer utils.GetCaptchaSolver().Shutdown()

	// Middleware stack (thứ tự: outermost → innermost)
	// Recovery → SecurityHeaders → RequestLogger → CORS → BodyLimit → Timeout → Router
	var h http.Handler = mux
	h = middleware.Timeout(120 * time.Second)(h) // 2 min cho login flows
	h = middleware.BodyLimit(1 << 20)(h) // 1MB
	h = middleware.CORS(cfg.AllowedOrigins)(h)
	h = middleware.RequestLogger(h)
	h = middleware.SecurityHeaders(h)
	h = middleware.Recovery(h)

	// Server với timeouts
	srv := &http.Server{
		Addr:         ":" + cfg.ServerPort,
		Handler:      h,
		ReadTimeout:  cfg.ReadTimeout,
		WriteTimeout: cfg.WriteTimeout,
		IdleTimeout:  cfg.IdleTimeout,
	}

	// Graceful shutdown
	done := make(chan os.Signal, 1)
	signal.Notify(done, os.Interrupt, syscall.SIGTERM)

	go func() {
		slog.Info("Server starting", "addr", srv.Addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("Server failed", "error", err)
			os.Exit(1)
		}
	}()

	<-done
	slog.Info("Server shutting down...")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		slog.Error("Server forced to shutdown", "error", err)
		os.Exit(1)
	}

	slog.Info("Server stopped gracefully")
}
