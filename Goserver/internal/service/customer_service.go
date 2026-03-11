package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"sort"
	"sync"
	"time"

	"goserver/internal/model"
	"goserver/pkg/utils"
)

// CustomerService xử lý upstream proxy cho customer/user data.
type CustomerService struct {
	cache *AgentCache
}

func NewCustomerService() *CustomerService {
	return &CustomerService{
		cache: GetAgentCache(),
	}
}

// ListCustomers fetch từ tất cả active agents, merge, sort, paginate.
func (s *CustomerService) ListCustomers(ctx context.Context, params *model.CustomerListParams) (*model.CustomerListResponse, error) {
	// Timeout tổng 20s — không chờ agent chậm quá lâu
	ctx, cancel := context.WithTimeout(ctx, 20*time.Second)
	defer cancel()

	agents := s.cache.ListActiveWithInfo()
	if len(agents) == 0 {
		return &model.CustomerListResponse{
			Data:  []model.UpstreamUser{},
			Total: 0,
			Page:  params.Page,
			Limit: params.Limit,
		}, nil
	}

	// Fetch song song từ tất cả agents
	type agentResult struct {
		users []model.UpstreamUser
		err   error
	}

	results := make([]agentResult, len(agents))
	var wg sync.WaitGroup

	for i, ag := range agents {
		wg.Add(1)
		go func(idx int, agent ActiveAgentInfo) {
			defer wg.Done()
			users, err := s.fetchFromAgent(ctx, agent, params)
			results[idx] = agentResult{users: users, err: err}
		}(i, ag)
	}

	wg.Wait()

	// Merge tất cả kết quả + dedup theo username
	seen := make(map[string]bool)
	var allUsers []model.UpstreamUser
	for i, r := range results {
		if r.err != nil {
			slog.Warn("Fetch agent failed, skipping",
				"agent_id", agents[i].ID,
				"agent_name", agents[i].Name,
				"error", r.err,
			)
			continue
		}
		for _, u := range r.users {
			if !seen[u.Username] {
				seen[u.Username] = true
				allUsers = append(allUsers, u)
			}
		}
	}

	// Sort
	sortUsers(allUsers, params.SortField, params.SortDir)

	// Paginate
	total := len(allUsers)
	start := (params.Page - 1) * params.Limit
	if start > total {
		start = total
	}
	end := start + params.Limit
	if end > total {
		end = total
	}

	page := allUsers[start:end]
	if page == nil {
		page = []model.UpstreamUser{}
	}

	return &model.CustomerListResponse{
		Data:  page,
		Total: total,
		Page:  params.Page,
		Limit: params.Limit,
	}, nil
}

// fetchFromAgent gọi upstream /agent/user.html cho 1 agent.
func (s *CustomerService) fetchFromAgent(ctx context.Context, agent ActiveAgentInfo, params *model.CustomerListParams) ([]model.UpstreamUser, error) {
	upstreamParams := map[string]string{
		"page":      "1",
		"limit":     "9999",
		"username":  params.Username,
		"user_type": "",
		"status":    params.Status,
	}

	resp, err := utils.FetchUpstreamWithEncrypt(
		ctx,
		agent.BaseURL,
		"/agent/user.html",
		agent.Cookie,
		agent.EncryptPublicKey,
		upstreamParams,
	)
	if err != nil {
		return nil, fmt.Errorf("agent %s: %w", agent.Name, err)
	}

	var users []model.UpstreamUser
	if err := json.Unmarshal(resp.Data, &users); err != nil {
		return nil, fmt.Errorf("agent %s: unmarshal: %w", agent.Name, err)
	}

	// Gắn agent_name
	for i := range users {
		users[i].AgentName = agent.Name
	}

	return users, nil
}

// sortUsers sort in-place theo field + direction.
func sortUsers(users []model.UpstreamUser, field, dir string) {
	if field == "" {
		field = "id"
	}
	if dir == "" {
		dir = "desc"
	}

	sort.Slice(users, func(i, j int) bool {
		var less bool
		switch field {
		case "username":
			less = users[i].Username < users[j].Username
		case "balance":
			less = users[i].Money < users[j].Money
		case "deposit_count":
			less = users[i].DepositCount < users[j].DepositCount
		case "withdrawal_count":
			less = users[i].WithdrawalCount < users[j].WithdrawalCount
		case "deposit_amount":
			less = users[i].DepositAmount < users[j].DepositAmount
		case "withdrawal_amount":
			less = users[i].WithdrawalAmount < users[j].WithdrawalAmount
		case "login_time":
			less = users[i].LoginTime < users[j].LoginTime
		case "register_time":
			less = users[i].RegisterTime < users[j].RegisterTime
		default: // "id"
			less = users[i].ID < users[j].ID
		}
		if dir == "desc" {
			return !less
		}
		return less
	})
}
