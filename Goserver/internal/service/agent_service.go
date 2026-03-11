package service

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log/slog"
	"strings"

	"goserver/internal/model"
	"goserver/internal/repository"
)

// AgentService xử lý CRUD cho agents.
type AgentService struct {
	agentRepo repository.AgentRepo
	cache     *AgentCache
}

func NewAgentService(agentRepo repository.AgentRepo) *AgentService {
	return &AgentService{
		agentRepo: agentRepo,
		cache:     GetAgentCache(),
	}
}

func (s *AgentService) ListAgents(ctx context.Context) ([]*model.AgentSafe, error) {
	agents, err := s.agentRepo.ListAll(ctx)
	if err != nil {
		return nil, err
	}
	result := make([]*model.AgentSafe, len(agents))
	for i, a := range agents {
		result[i] = a.ToSafe()
	}
	return result, nil
}

func (s *AgentService) GetAgent(ctx context.Context, id int64) (*model.AgentSafe, error) {
	agent, err := s.agentRepo.FindByID(ctx, id)
	if err != nil {
		if errors.Is(err, repository.ErrAgentNotFound) {
			return nil, model.NewBadRequest("Agent không tồn tại")
		}
		return nil, err
	}
	return agent.ToSafe(), nil
}

func (s *AgentService) CreateAgent(ctx context.Context, req *model.CreateAgentRequest) (*model.AgentSafe, error) {
	// Validate
	req.Name = strings.TrimSpace(req.Name)
	req.ExtUsername = strings.TrimSpace(req.ExtUsername)
	req.ExtPassword = strings.TrimSpace(req.ExtPassword)
	req.BaseURL = strings.TrimSpace(req.BaseURL)

	if req.Name == "" {
		return nil, model.NewBadRequest("Tên đại lý không được trống")
	}
	if req.ExtUsername == "" {
		return nil, model.NewBadRequest("Tài khoản EE88 không được trống")
	}
	if req.ExtPassword == "" {
		return nil, model.NewBadRequest("Mật khẩu EE88 không được trống")
	}

	// Check duplicate
	if _, err := s.agentRepo.FindByExtUsername(ctx, req.ExtUsername); err == nil {
		return nil, model.NewConflict(fmt.Sprintf("Tài khoản EE88 '%s' đã tồn tại", req.ExtUsername))
	}

	agent := &model.Agent{
		Name:        req.Name,
		ExtUsername: req.ExtUsername,
		ExtPassword: req.ExtPassword,
	}
	if req.BaseURL != "" {
		agent.BaseURL = sql.NullString{String: req.BaseURL, Valid: true}
	}

	created, err := s.agentRepo.Create(ctx, agent)
	if err != nil {
		if errors.Is(err, repository.ErrAgentUsernameExists) {
			return nil, model.NewConflict(fmt.Sprintf("Tài khoản EE88 '%s' đã tồn tại", req.ExtUsername))
		}
		return nil, err
	}

	s.cache.Set(created.ID, created)
	slog.Info("Agent đã được tạo", "agent_id", created.ID, "name", req.Name)
	return created.ToSafe(), nil
}

func (s *AgentService) UpdateAgent(ctx context.Context, id int64, req *model.UpdateAgentRequest) (*model.AgentSafe, error) {
	if _, err := s.agentRepo.FindByID(ctx, id); err != nil {
		if errors.Is(err, repository.ErrAgentNotFound) {
			return nil, model.NewBadRequest("Agent không tồn tại")
		}
		return nil, err
	}

	fields := make(map[string]interface{})

	if req.Name != nil {
		name := strings.TrimSpace(*req.Name)
		if name == "" {
			return nil, model.NewBadRequest("Tên đại lý không được trống")
		}
		fields["name"] = name
	}
	if req.ExtPassword != nil {
		pwd := strings.TrimSpace(*req.ExtPassword)
		if pwd == "" {
			return nil, model.NewBadRequest("Mật khẩu không được trống")
		}
		fields["ext_password"] = pwd
	}
	if req.BaseURL != nil {
		url := strings.TrimSpace(*req.BaseURL)
		if url == "" {
			fields["base_url"] = sql.NullString{}
		} else {
			fields["base_url"] = sql.NullString{String: url, Valid: true}
		}
	}
	if req.IsActive != nil {
		fields["is_active"] = *req.IsActive
		if !*req.IsActive {
			fields["status"] = "offline"
		}
	}
	if req.AutoLogin != nil {
		fields["auto_login"] = *req.AutoLogin
	}

	if len(fields) == 0 {
		return s.GetAgent(ctx, id)
	}

	agent, err := s.agentRepo.Update(ctx, id, fields)
	if err != nil {
		return nil, err
	}
	s.cache.Set(id, agent)

	slog.Info("Agent đã được cập nhật", "agent_id", id)
	return agent.ToSafe(), nil
}

func (s *AgentService) DeactivateAgent(ctx context.Context, id int64) error {
	if _, err := s.agentRepo.FindByID(ctx, id); err != nil {
		if errors.Is(err, repository.ErrAgentNotFound) {
			return model.NewBadRequest("Agent không tồn tại")
		}
		return err
	}

	updated, err := s.agentRepo.Update(ctx, id, map[string]interface{}{
		"is_active": false,
		"status":    "offline",
	})
	if err != nil {
		return err
	}
	if updated != nil {
		s.cache.Set(id, updated)
	}

	slog.Info("Agent đã bị vô hiệu hoá", "agent_id", id)
	return nil
}

func (s *AgentService) DeleteAgent(ctx context.Context, id int64) error {
	if err := s.agentRepo.Delete(ctx, id); err != nil {
		if errors.Is(err, repository.ErrAgentNotFound) {
			return model.NewBadRequest("Agent không tồn tại")
		}
		return err
	}
	s.cache.Delete(id)
	slog.Info("Agent đã bị xoá", "agent_id", id)
	return nil
}
