package service

import (
	"context"
	"log/slog"
	"time"

	"goserver/internal/repository"
)

// ============================================================================
// Scheduler — chạy nền kiểm tra cookie health + auto-relogin.
// Fix MAXHUB: không có health check scheduler → cookie hết hạn âm thầm.
// ============================================================================

const (
	healthCheckInterval = 1 * time.Hour  // Check cookie health mỗi 1 giờ
	autoLoginInterval   = 30 * time.Minute // Auto-login agents có auto_login=true
)

type Scheduler struct {
	loginService *EE88LoginService
	agentRepo    repository.AgentRepo
	stopCh       chan struct{}
}

func NewScheduler(loginService *EE88LoginService, agentRepo repository.AgentRepo) *Scheduler {
	return &Scheduler{
		loginService: loginService,
		agentRepo:    agentRepo,
		stopCh:       make(chan struct{}),
	}
}

func (s *Scheduler) Start() {
	go s.runHealthCheck()
	go s.runAutoLogin()
	slog.Info("Scheduler started", "health_check_interval", healthCheckInterval, "auto_login_interval", autoLoginInterval)
}

func (s *Scheduler) Stop() {
	close(s.stopCh)
	slog.Info("Scheduler stopped")
}

func (s *Scheduler) runHealthCheck() {
	// Chờ 30s sau khi server start trước khi check lần đầu
	timer := time.NewTimer(30 * time.Second)
	defer timer.Stop()

	for {
		select {
		case <-s.stopCh:
			return
		case <-timer.C:
			s.doHealthCheck()
			timer.Reset(healthCheckInterval)
		}
	}
}

func (s *Scheduler) doHealthCheck() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	results, err := s.loginService.CheckCookieHealth(ctx)
	if err != nil {
		slog.Error("Health check thất bại", "error", err)
		return
	}

	alive := 0
	dead := 0
	for _, r := range results {
		if r.Alive {
			alive++
		} else {
			dead++
			slog.Warn("Agent cookie không hợp lệ", "agent_id", r.ID, "name", r.Name)
		}
	}
	slog.Info("Health check hoàn tất", "alive", alive, "dead", dead, "total", len(results))
}

func (s *Scheduler) runAutoLogin() {
	// Chờ 1 phút sau khi server start
	timer := time.NewTimer(1 * time.Minute)
	defer timer.Stop()

	for {
		select {
		case <-s.stopCh:
			return
		case <-timer.C:
			s.doAutoLogin()
			timer.Reset(autoLoginInterval)
		}
	}
}

func (s *Scheduler) doAutoLogin() {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()

	// Chỉ auto-login agents có auto_login=true và đang offline/error
	agents, err := s.agentRepo.ListNeedLogin(ctx)
	if err != nil {
		slog.Error("Auto-login list thất bại", "error", err)
		return
	}

	count := 0
	for _, agent := range agents {
		if !agent.AutoLogin {
			continue
		}
		count++
		_, err := s.loginService.LoginAgent(ctx, agent.ID, "scheduler", "")
		if err != nil {
			slog.Warn("Auto-login thất bại", "agent_id", agent.ID, "error", err)
		}
	}

	if count > 0 {
		slog.Info("Auto-login scheduler hoàn tất", "processed", count)
	}
}
