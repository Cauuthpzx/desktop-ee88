package service

import (
	"context"
	"encoding/json"
	"sort"

	"goserver/internal/model"
)

// CustomerService — customer list sử dụng ProxyService để fetch parallel all agents.
type CustomerService struct {
	proxy *ProxyService
}

func NewCustomerService(proxy *ProxyService) *CustomerService {
	return &CustomerService{
		proxy: proxy,
	}
}

// ListCustomers fetch từ ALL agents song song (qua ProxyService), decode → sort → paginate.
func (s *CustomerService) ListCustomers(ctx context.Context, params *model.CustomerListParams) (*model.CustomerListResponse, error) {
	// Fetch ALL data qua proxy (parallel all agents, cached, multi-page)
	proxyResp, err := s.proxy.FetchAll(ctx, &ProxyParams{
		Path: "/agent/user.html",
		Params: map[string]string{
			"username":  params.Username,
			"user_type": "",
			"status":    params.Status,
		},
		Page:  1,
		Limit: 999999, // Lấy hết để sort local
	})
	if err != nil {
		return nil, err
	}

	// Decode raw items → UpstreamUser
	var users []model.UpstreamUser
	if err := json.Unmarshal(proxyResp.Data, &users); err != nil {
		return &model.CustomerListResponse{
			Data:  []model.UpstreamUser{},
			Total: 0,
			Page:  params.Page,
			Limit: params.Limit,
		}, nil
	}

	// Sort
	sortUsers(users, params.SortField, params.SortDir)

	// Paginate local
	total := len(users)
	start := (params.Page - 1) * params.Limit
	if start > total {
		start = total
	}
	end := start + params.Limit
	if end > total {
		end = total
	}

	page := users[start:end]
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
