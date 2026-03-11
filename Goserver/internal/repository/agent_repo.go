package repository

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	"goserver/internal/model"

	"github.com/jmoiron/sqlx"
	"github.com/lib/pq"
)

var (
	ErrAgentNotFound    = errors.New("agent không tồn tại")
	ErrAgentUsernameExists = errors.New("ext_username đã tồn tại")
)

type AgentRepo interface {
	Create(ctx context.Context, agent *model.Agent) (*model.Agent, error)
	FindByID(ctx context.Context, id int64) (*model.Agent, error)
	FindByExtUsername(ctx context.Context, username string) (*model.Agent, error)
	ListAll(ctx context.Context) ([]*model.Agent, error)
	ListActive(ctx context.Context) ([]*model.Agent, error)
	ListNeedLogin(ctx context.Context) ([]*model.Agent, error)
	Update(ctx context.Context, id int64, fields map[string]interface{}) (*model.Agent, error)
	Delete(ctx context.Context, id int64) error
	IncrementLoginAttempts(ctx context.Context, id int64, loginError string) error

	CreateLoginHistory(ctx context.Context, h *model.AgentLoginHistory) error
	ListLoginHistory(ctx context.Context, agentID int64, limit int) ([]*model.AgentLoginHistory, error)
}

type agentRepository struct {
	db *sqlx.DB
}

func NewAgentRepository(db *sqlx.DB) AgentRepo {
	return &agentRepository{db: db}
}

func (r *agentRepository) Create(ctx context.Context, agent *model.Agent) (*model.Agent, error) {
	query := `
		INSERT INTO agents (name, ext_username, ext_password, base_url, session_cookie, status, is_active, auto_login)
		VALUES ($1, $2, $3, $4, '', 'offline', true, $5)
		RETURNING id, name, ext_username, ext_password, base_url, session_cookie,
		          encrypt_public_key, cookie_expires, status, is_active, login_error,
		          login_attempts, last_login_at, auto_login, created_at, updated_at`

	var baseURL sql.NullString
	if agent.BaseURL.Valid {
		baseURL = agent.BaseURL
	}

	row := r.db.QueryRowxContext(ctx, query,
		agent.Name, agent.ExtUsername, agent.ExtPassword, baseURL, agent.AutoLogin)

	var result model.Agent
	if err := row.StructScan(&result); err != nil {
		if pqErr, ok := err.(*pq.Error); ok && pqErr.Code == "23505" {
			return nil, ErrAgentUsernameExists
		}
		return nil, fmt.Errorf("insert agent: %w", err)
	}
	return &result, nil
}

func (r *agentRepository) FindByID(ctx context.Context, id int64) (*model.Agent, error) {
	var agent model.Agent
	err := r.db.GetContext(ctx, &agent,
		`SELECT * FROM agents WHERE id = $1`, id)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrAgentNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("find agent by id: %w", err)
	}
	return &agent, nil
}

func (r *agentRepository) FindByExtUsername(ctx context.Context, username string) (*model.Agent, error) {
	var agent model.Agent
	err := r.db.GetContext(ctx, &agent,
		`SELECT * FROM agents WHERE ext_username = $1`, username)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrAgentNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("find agent by ext_username: %w", err)
	}
	return &agent, nil
}

func (r *agentRepository) ListAll(ctx context.Context) ([]*model.Agent, error) {
	var agents []*model.Agent
	err := r.db.SelectContext(ctx, &agents,
		`SELECT * FROM agents ORDER BY name ASC`)
	if err != nil {
		return nil, fmt.Errorf("list agents: %w", err)
	}
	return agents, nil
}

func (r *agentRepository) ListActive(ctx context.Context) ([]*model.Agent, error) {
	var agents []*model.Agent
	err := r.db.SelectContext(ctx, &agents,
		`SELECT * FROM agents WHERE is_active = true AND status = 'active' ORDER BY name ASC`)
	if err != nil {
		return nil, fmt.Errorf("list active agents: %w", err)
	}
	return agents, nil
}

// ListNeedLogin trả agents cần login: active, có password, status offline/error hoặc cookie hết hạn.
func (r *agentRepository) ListNeedLogin(ctx context.Context) ([]*model.Agent, error) {
	var agents []*model.Agent
	err := r.db.SelectContext(ctx, &agents, `
		SELECT * FROM agents
		WHERE is_active = true
		  AND ext_password != ''
		  AND (status IN ('offline', 'error') OR cookie_expires < NOW())
		ORDER BY name ASC`)
	if err != nil {
		return nil, fmt.Errorf("list need-login agents: %w", err)
	}
	return agents, nil
}

func (r *agentRepository) Update(ctx context.Context, id int64, fields map[string]interface{}) (*model.Agent, error) {
	if len(fields) == 0 {
		return r.FindByID(ctx, id)
	}

	setClauses := make([]string, 0, len(fields)+1)
	args := make([]interface{}, 0, len(fields)+1)
	i := 1

	for col, val := range fields {
		setClauses = append(setClauses, fmt.Sprintf("%s = $%d", col, i))
		args = append(args, val)
		i++
	}

	// Luôn update updated_at
	setClauses = append(setClauses, fmt.Sprintf("updated_at = $%d", i))
	args = append(args, time.Now())
	i++

	args = append(args, id)
	query := fmt.Sprintf(
		`UPDATE agents SET %s WHERE id = $%d
		 RETURNING id, name, ext_username, ext_password, base_url, session_cookie,
		           encrypt_public_key, cookie_expires, status, is_active, login_error,
		           login_attempts, last_login_at, auto_login, created_at, updated_at`,
		strings.Join(setClauses, ", "), i,
	)

	var agent model.Agent
	if err := r.db.GetContext(ctx, &agent, query, args...); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, ErrAgentNotFound
		}
		return nil, fmt.Errorf("update agent: %w", err)
	}
	return &agent, nil
}

func (r *agentRepository) Delete(ctx context.Context, id int64) error {
	result, err := r.db.ExecContext(ctx, `DELETE FROM agents WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("delete agent: %w", err)
	}
	rows, _ := result.RowsAffected()
	if rows == 0 {
		return ErrAgentNotFound
	}
	return nil
}

func (r *agentRepository) IncrementLoginAttempts(ctx context.Context, id int64, loginError string) error {
	_, err := r.db.ExecContext(ctx, `
		UPDATE agents SET
			status = 'error',
			login_error = $2,
			login_attempts = login_attempts + 1,
			updated_at = NOW()
		WHERE id = $1`, id, loginError)
	return err
}

func (r *agentRepository) CreateLoginHistory(ctx context.Context, h *model.AgentLoginHistory) error {
	_, err := r.db.ExecContext(ctx, `
		INSERT INTO agent_login_history (agent_id, success, captcha_attempts, error_message, ip_address, triggered_by)
		VALUES ($1, $2, $3, $4, $5, $6)`,
		h.AgentID, h.Success, h.CaptchaAttempts,
		h.ErrorMessage, h.IPAddress, h.TriggeredBy)
	return err
}

func (r *agentRepository) ListLoginHistory(ctx context.Context, agentID int64, limit int) ([]*model.AgentLoginHistory, error) {
	if limit <= 0 || limit > 100 {
		limit = 20
	}
	var history []*model.AgentLoginHistory
	err := r.db.SelectContext(ctx, &history, `
		SELECT * FROM agent_login_history
		WHERE agent_id = $1
		ORDER BY created_at DESC
		LIMIT $2`, agentID, limit)
	if err != nil {
		return nil, fmt.Errorf("list login history: %w", err)
	}
	return history, nil
}
