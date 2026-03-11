package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"goserver/pkg/utils"
)

// ProxyService — generic upstream proxy: fetch từ tất cả agents, merge, paginate.
type ProxyService struct {
	cache *AgentCache
}

func NewProxyService() *ProxyService {
	return &ProxyService{cache: GetAgentCache()}
}

// ProxyParams chứa query params generic cho upstream proxy call.
type ProxyParams struct {
	Path   string            // upstream path, vd: "/agent/betLottery.html"
	Params map[string]string // upstream query params
	Page   int
	Limit  int
}

// ProxyResponse — response trả cho client.
type ProxyResponse struct {
	Data      json.RawMessage        `json:"data"`
	Total     int                    `json:"total"`
	Page      int                    `json:"page"`
	Limit     int                    `json:"limit"`
	Count     int                    `json:"count"`
	TotalData map[string]interface{} `json:"total_data,omitempty"`
}

// FetchAll gọi upstream từ tất cả active agents, merge data arrays.
// Dùng cho các trang cần aggregate data từ nhiều agents (bets, reports, etc.)
func (s *ProxyService) FetchAll(ctx context.Context, p *ProxyParams) (*ProxyResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 20*time.Second)
	defer cancel()

	agents := s.cache.ListActiveWithInfo()
	if len(agents) == 0 {
		return &ProxyResponse{
			Data:  json.RawMessage("[]"),
			Total: 0,
			Page:  p.Page,
			Limit: p.Limit,
		}, nil
	}

	type agentResult struct {
		resp *utils.UpstreamResponse
		err  error
	}

	results := make([]agentResult, len(agents))
	var wg sync.WaitGroup

	for i, ag := range agents {
		wg.Add(1)
		go func(idx int, agent ActiveAgentInfo) {
			defer wg.Done()
			resp, err := utils.FetchUpstreamWithEncrypt(
				ctx,
				agent.BaseURL,
				p.Path,
				agent.Cookie,
				agent.EncryptPublicKey,
				p.Params,
			)
			results[idx] = agentResult{resp: resp, err: err}
		}(i, ag)
	}

	wg.Wait()

	// Merge data arrays từ tất cả agents
	var allItems []json.RawMessage
	var totalData map[string]interface{}
	totalCount := 0

	for i, r := range results {
		if r.err != nil {
			slog.Warn("Proxy fetch failed, skipping",
				"agent_id", agents[i].ID,
				"agent_name", agents[i].Name,
				"path", p.Path,
				"error", r.err,
			)
			continue
		}

		// Parse data array
		var items []json.RawMessage
		if err := json.Unmarshal(r.resp.Data, &items); err != nil {
			slog.Warn("Proxy parse data failed",
				"agent_name", agents[i].Name,
				"path", p.Path,
				"error", err,
			)
			continue
		}

		allItems = append(allItems, items...)
		totalCount += r.resp.Count

		// Merge total_data — lấy cái đầu tiên có data
		if totalData == nil && r.resp.TotalData != nil {
			totalData = r.resp.TotalData
		}
	}

	// Paginate in-memory
	total := len(allItems)
	start := (p.Page - 1) * p.Limit
	if start > total {
		start = total
	}
	end := start + p.Limit
	if end > total {
		end = total
	}

	page := allItems[start:end]
	if page == nil {
		page = []json.RawMessage{}
	}

	pageJSON, _ := json.Marshal(page)

	return &ProxyResponse{
		Data:      pageJSON,
		Total:     total,
		Page:      p.Page,
		Limit:     p.Limit,
		Count:     totalCount,
		TotalData: totalData,
	}, nil
}

// FetchFirst gọi upstream từ agent đầu tiên có cookie (dùng cho endpoints không cần merge).
func (s *ProxyService) FetchFirst(ctx context.Context, p *ProxyParams) (*ProxyResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 15*time.Second)
	defer cancel()

	agents := s.cache.ListActiveWithInfo()
	if len(agents) == 0 {
		return nil, fmt.Errorf("không có agent active")
	}

	// Thử từng agent cho đến khi thành công
	for _, ag := range agents {
		resp, err := utils.FetchUpstreamWithEncrypt(
			ctx,
			ag.BaseURL,
			p.Path,
			ag.Cookie,
			ag.EncryptPublicKey,
			p.Params,
		)
		if err != nil {
			slog.Warn("Proxy fetch failed, trying next",
				"agent_name", ag.Name,
				"path", p.Path,
				"error", err,
			)
			continue
		}

		return &ProxyResponse{
			Data:      resp.Data,
			Total:     resp.Count,
			Page:      p.Page,
			Limit:     p.Limit,
			Count:     resp.Count,
			TotalData: resp.TotalData,
		}, nil
	}

	return nil, fmt.Errorf("tất cả agents đều thất bại cho %s", p.Path)
}
