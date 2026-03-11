package service

import (
	"context"
	"log/slog"
	"sync"
	"time"

	"goserver/internal/model"
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

	// Lọc agents cần login
	var candidates []*model.Agent
	for _, agent := range agents {
		if agent.AutoLogin {
			candidates = append(candidates, agent)
		}
	}
	if len(candidates) == 0 {
		return
	}

	slog.Info("Auto-login bắt đầu", "candidates", len(candidates))

	// Bước 1: Check cookie live trước — tránh login chồng đè khi nhiều client cùng dùng
	var needLogin []int64
	for _, agent := range candidates {
		// Nếu agent có cookie trong DB, check xem còn sống không
		if agent.SessionCookie != "" {
			valid, _, checkErr := s.loginService.CheckAgentSession(ctx, agent.ID)
			if checkErr == nil && valid {
				slog.Info("Auto-login skip: cookie còn sống", "agent_id", agent.ID, "name", agent.Name)
				continue
			}
		}
		needLogin = append(needLogin, agent.ID)
	}

	if len(needLogin) == 0 {
		slog.Info("Auto-login: tất cả cookie còn sống, không cần login")
		return
	}

	slog.Info("Auto-login sau check live", "need_login", len(needLogin), "skipped", len(candidates)-len(needLogin))

	// Bước 2: Login các agent thực sự cần
	var wg sync.WaitGroup
	var mu sync.Mutex
	success, failed := 0, 0

	for _, agentID := range needLogin {
		wg.Add(1)
		go func(id int64) {
			defer wg.Done()
			defer func() {
				if r := recover(); r != nil {
					mu.Lock()
					failed++
					mu.Unlock()
					slog.Error("Auto-login panic", "agent_id", id, "panic", r)
				}
			}()
			_, loginErr := s.loginService.LoginAgent(ctx, id, "scheduler", "")
			mu.Lock()
			if loginErr != nil {
				failed++
				slog.Warn("Auto-login thất bại", "agent_id", id, "error", loginErr)
			} else {
				success++
			}
			mu.Unlock()
		}(agentID)
	}

	wg.Wait()
	slog.Info("Auto-login scheduler hoàn tất", "success", success, "failed", failed, "total", len(needLogin))
}
