package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"goserver/internal/cache"
	"goserver/pkg/utils"
)

// ============================================================================
// ProxyService — upstream proxy matching C++ UpstreamClient logic:
//   1. Parallel fetch ALL agents → merge data
//   2. Per-agent cache (30s fresh, 2min stale)
//   3. Merged cache — tránh merge lại khi đổi trang
//   4. Stale-while-revalidate — trả stale ngay, refresh background
//   5. Multi-page: fetch thêm pages khi count > 10000
// ============================================================================

type ProxyService struct {
	agentCache *AgentCache
	redis      *cache.RedisCache

	// Per-agent upstream data cache
	dataCacheMu sync.RWMutex
	dataCache   map[string]*agentDataEntry

	// Merged cache — all agents merged
	mergedCacheMu sync.RWMutex
	mergedCache   map[string]*mergedCacheEntry

	// Track background revalidation (tránh duplicate)
	revalidatingMu sync.Mutex
	revalidating   map[string]bool
}

// agentDataEntry — cached data cho 1 agent + 1 path + params.
type agentDataEntry struct {
	items     []json.RawMessage
	count     int
	totalData map[string]interface{}
	createdAt time.Time
}

// mergedCacheEntry — cached merged data từ tất cả agents.
type mergedCacheEntry struct {
	AllItems  []json.RawMessage        `json:"items"`
	Count     int                      `json:"count"`
	TotalData map[string]interface{}   `json:"total_data,omitempty"`
	createdAt time.Time
}

const (
	upstreamPageSize    = 10000
	maxUpstreamPages    = 10  // Max 100k records per agent
	cacheFreshTTL       = 30 * time.Second
	cacheStaleTTL       = 2 * time.Minute
	maxMergedCacheItems = 50
)

func NewProxyService(redisCache *cache.RedisCache) *ProxyService {
	return &ProxyService{
		agentCache:   GetAgentCache(),
		redis:        redisCache,
		dataCache:    make(map[string]*agentDataEntry),
		mergedCache:  make(map[string]*mergedCacheEntry),
		revalidating: make(map[string]bool),
	}
}

// ProxyParams chứa query params generic cho upstream proxy call.
type ProxyParams struct {
	Path   string            // upstream path, vd: "/agent/bet.html"
	Params map[string]string // upstream query params (filter only, no page/limit)
	Page   int               // client page
	Limit  int               // client limit
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

// ── Cache key builders (match C++ logic: exclude page/limit) ──

func buildParamsSuffix(params map[string]string) string {
	// Sort keys for consistent cache key
	keys := make([]string, 0, len(params))
	for k := range params {
		if k == "page" || k == "limit" {
			continue
		}
		keys = append(keys, k)
	}
	sort.Strings(keys)

	var b strings.Builder
	for _, k := range keys {
		b.WriteString(k)
		b.WriteByte('=')
		b.WriteString(params[k])
		b.WriteByte('&')
	}
	return b.String()
}

func makeAgentCacheKey(agentID int64, path string, params map[string]string) string {
	return fmt.Sprintf("%d:%s:%s", agentID, path, buildParamsSuffix(params))
}

func makeMergedCacheKey(path string, params map[string]string) string {
	return path + ":" + buildParamsSuffix(params)
}

// ── FetchAll — entry point chính (match C++ fetch_all) ──
//
// Chiến lược tốc độ:
//   1. Merged cache FRESH  → paginate O(limit), trả ngay      (~0ms)
//   2. Merged cache STALE  → trả stale ngay + revalidate bg   (~0ms)
//   3. Cache MISS          → fetch all agents → build cache    (~500-2000ms)

func (s *ProxyService) FetchAll(ctx context.Context, p *ProxyParams) (*ProxyResponse, error) {
	agents := s.agentCache.ListActiveWithInfo()
	slog.Info("FetchAll", "path", p.Path, "active_agents", len(agents), "page", p.Page, "limit", p.Limit)
	if len(agents) == 0 {
		return &ProxyResponse{
			Data:  json.RawMessage("[]"),
			Total: 0,
			Page:  p.Page,
			Limit: p.Limit,
		}, nil
	}

	s.evictExpiredCache()

	mergedKey := makeMergedCacheKey(p.Path, p.Params)

	// Check merged cache
	s.mergedCacheMu.RLock()
	cached, hasCached := s.mergedCache[mergedKey]
	s.mergedCacheMu.RUnlock()

	if hasCached {
		age := time.Since(cached.createdAt)

		if age <= cacheFreshTTL {
			// FRESH — trả ngay
			return s.paginateFromMerged(cached, p.Page, p.Limit), nil
		}

		if age <= cacheStaleTTL {
			// STALE — trả ngay + background revalidate
			slog.Debug("Stale-while-revalidate", "path", p.Path, "age_ms", age.Milliseconds())
			resp := s.paginateFromMerged(cached, p.Page, p.Limit)
			go s.revalidateBackground(p.Path, p.Params)
			return resp, nil
		}

		// Quá stale — xoá
		s.mergedCacheMu.Lock()
		delete(s.mergedCache, mergedKey)
		s.mergedCacheMu.Unlock()
	}

	// L2: Check Redis before upstream fetch
	if s.redis != nil {
		if data, ok := s.redis.Get(ctx, "proxy:"+mergedKey); ok {
			var redisCached mergedCacheEntry
			if err := json.Unmarshal(data, &redisCached); err == nil {
				slog.Debug("Redis L2 HIT", "path", p.Path)
				// Promote to L1 memory cache
				redisCached.createdAt = time.Now()
				s.mergedCacheMu.Lock()
				s.mergedCache[mergedKey] = &redisCached
				s.mergedCacheMu.Unlock()
				// Background revalidate to keep fresh
				go s.revalidateBackground(p.Path, p.Params)
				return s.paginateFromMerged(&redisCached, p.Page, p.Limit), nil
			}
		}
	}

	// MISS — fetch tất cả agents
	merged, err := s.fetchAllInternal(ctx, p.Path, p.Params, agents)
	if err != nil {
		return nil, err
	}

	return s.paginateFromMerged(merged, p.Page, p.Limit), nil
}

// FetchFirst gọi upstream từ agent đầu tiên thành công (dùng cho endpoints đơn giản).
func (s *ProxyService) FetchFirst(ctx context.Context, p *ProxyParams) (*ProxyResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 15*time.Second)
	defer cancel()

	agents := s.agentCache.ListActiveWithInfo()
	if len(agents) == 0 {
		return nil, fmt.Errorf("không có agent active")
	}

	upParams := make(map[string]string, len(p.Params)+2)
	for k, v := range p.Params {
		upParams[k] = v
	}
	upParams["page"] = strconv.Itoa(p.Page)
	upParams["limit"] = strconv.Itoa(p.Limit)

	for _, ag := range agents {
		resp, err := utils.FetchUpstreamWithEncrypt(
			ctx, ag.BaseURL, p.Path, ag.Cookie, ag.EncryptPublicKey, upParams,
		)
		if err != nil {
			slog.Warn("Proxy fetch failed, trying next",
				"agent_name", ag.Name, "path", p.Path, "error", err)
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

// ── paginateFromMerged — O(limit) slice từ merged cache ──

func (s *ProxyService) paginateFromMerged(merged *mergedCacheEntry, page, limit int) *ProxyResponse {
	fetched := len(merged.AllItems)
	total := merged.Count
	if fetched > total {
		total = fetched
	}

	start := (page - 1) * limit
	if start > fetched {
		start = fetched
	}
	end := start + limit
	if end > fetched {
		end = fetched
	}

	pageItems := merged.AllItems[start:end]
	if pageItems == nil {
		pageItems = []json.RawMessage{}
	}

	pageJSON, _ := json.Marshal(pageItems)

	return &ProxyResponse{
		Data:      pageJSON,
		Total:     total,
		Page:      page,
		Limit:     limit,
		Count:     merged.Count,
		TotalData: merged.TotalData,
	}
}

// ── fetchAllInternal — core: parallel fetch ALL agents → merge → cache ──
// Match C++ fetch_all_internal exactly.

func (s *ProxyService) fetchAllInternal(ctx context.Context, path string, params map[string]string, agents []ActiveAgentInfo) (*mergedCacheEntry, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	type agentResult struct {
		items     []json.RawMessage
		count     int
		totalData map[string]interface{}
		err       error
	}

	results := make([]agentResult, len(agents))
	var wg sync.WaitGroup

	for i, ag := range agents {
		// Check per-agent cache first
		agentKey := makeAgentCacheKey(ag.ID, path, params)
		s.dataCacheMu.RLock()
		agentCached, hasAgentCache := s.dataCache[agentKey]
		s.dataCacheMu.RUnlock()

		if hasAgentCache && time.Since(agentCached.createdAt) <= cacheFreshTTL {
			results[i] = agentResult{
				items:     agentCached.items,
				count:     agentCached.count,
				totalData: agentCached.totalData,
			}
			continue
		}

		// Fetch from upstream
		wg.Add(1)
		go func(idx int, agent ActiveAgentInfo) {
			defer wg.Done()
			items, count, totalData, err := s.fetchFromAgent(ctx, agent, path, params)
			results[idx] = agentResult{
				items:     items,
				count:     count,
				totalData: totalData,
				err:       err,
			}

			// Cache per-agent result on success
			if err == nil {
				ak := makeAgentCacheKey(agent.ID, path, params)
				s.dataCacheMu.Lock()
				s.dataCache[ak] = &agentDataEntry{
					items:     items,
					count:     count,
					totalData: totalData,
					createdAt: time.Now(),
				}
				s.dataCacheMu.Unlock()
			}
		}(i, ag)
	}
	wg.Wait()

	// Merge all agent results
	var allItems []json.RawMessage
	totalData := make(map[string]interface{})

	successCount := 0
	for i, r := range results {
		if r.err != nil {
			slog.Warn("Agent fetch failed (skipped)", "agent_index", i, "error", r.err)
			continue
		}
		slog.Info("Agent fetch OK", "agent_index", i, "items", len(r.items), "count", r.count)
		successCount++
		allItems = append(allItems, r.items...)
		// Cộng dồn totalData từ tất cả agents (sum numeric fields)
		for k, v := range r.totalData {
			mergeTotalDataField(totalData, k, v)
		}
	}
	// Total = số items thực tế sau merge (không cộng dồn count upstream)
	totalCount := len(allItems)
	slog.Info("Merge done", "path", path, "success_agents", successCount, "total_items", totalCount)

	if allItems == nil {
		allItems = []json.RawMessage{}
	}
	if len(totalData) == 0 {
		totalData = nil
	}

	// Build merged cache
	merged := &mergedCacheEntry{
		AllItems:  allItems,
		Count:     totalCount,
		TotalData: totalData,
		createdAt: time.Now(),
	}

	mergedKey := makeMergedCacheKey(path, params)
	s.mergedCacheMu.Lock()
	s.mergedCache[mergedKey] = merged
	s.mergedCacheMu.Unlock()

	// Write to Redis L2 (fire-and-forget, non-blocking)
	if s.redis != nil {
		go func() {
			data, err := json.Marshal(merged)
			if err == nil {
				s.redis.Set(context.Background(), "proxy:"+mergedKey, data, 0)
			}
		}()
	}

	return merged, nil
}

// ── fetchFromAgent — fetch ALL data từ 1 agent (multi-page nếu cần) ──

func (s *ProxyService) fetchFromAgent(ctx context.Context, agent ActiveAgentInfo, path string, filterParams map[string]string) ([]json.RawMessage, int, map[string]interface{}, error) {
	// Build upstream params: filter + page=1, limit=10000
	upParams := make(map[string]string, len(filterParams)+2)
	for k, v := range filterParams {
		upParams[k] = v
	}
	upParams["page"] = "1"
	upParams["limit"] = strconv.Itoa(upstreamPageSize)

	// Fetch page 1
	resp, err := utils.FetchUpstreamWithEncrypt(
		ctx, agent.BaseURL, path, agent.Cookie, agent.EncryptPublicKey, upParams,
	)
	if err != nil {
		return nil, 0, nil, fmt.Errorf("agent %s: %w", agent.Name, err)
	}

	var items []json.RawMessage
	if err := json.Unmarshal(resp.Data, &items); err != nil {
		return nil, 0, nil, fmt.Errorf("agent %s: unmarshal page 1: %w", agent.Name, err)
	}

	totalCount := resp.Count
	totalData := resp.TotalData

	// Nếu còn data → fetch thêm pages song song (match C++ logic)
	if totalCount > upstreamPageSize && len(items) >= upstreamPageSize {
		totalPages := (totalCount + upstreamPageSize - 1) / upstreamPageSize
		if totalPages > maxUpstreamPages {
			totalPages = maxUpstreamPages
		}

		type pageResult struct {
			items []json.RawMessage
			err   error
		}
		pageResults := make([]pageResult, totalPages-1)
		var wg sync.WaitGroup

		for p := 2; p <= totalPages; p++ {
			wg.Add(1)
			go func(page int) {
				defer wg.Done()
				extraParams := make(map[string]string, len(filterParams)+2)
				for k, v := range filterParams {
					extraParams[k] = v
				}
				extraParams["page"] = strconv.Itoa(page)
				extraParams["limit"] = strconv.Itoa(upstreamPageSize)

				r, fetchErr := utils.FetchUpstreamWithEncrypt(
					ctx, agent.BaseURL, path, agent.Cookie, agent.EncryptPublicKey, extraParams,
				)
				if fetchErr != nil {
					pageResults[page-2] = pageResult{err: fetchErr}
					return
				}
				var pageItems []json.RawMessage
				if unmarshalErr := json.Unmarshal(r.Data, &pageItems); unmarshalErr != nil {
					pageResults[page-2] = pageResult{err: unmarshalErr}
					return
				}
				pageResults[page-2] = pageResult{items: pageItems}
			}(p)
		}
		wg.Wait()

		for _, r := range pageResults {
			if r.err != nil {
				slog.Warn("Fetch extra page failed", "agent", agent.Name, "error", r.err)
				continue
			}
			items = append(items, r.items...)
		}
	}

	return items, totalCount, totalData, nil
}

// ── Background revalidate (match C++ revalidate_background) ──

func (s *ProxyService) revalidateBackground(path string, params map[string]string) {
	mergedKey := makeMergedCacheKey(path, params)

	s.revalidatingMu.Lock()
	if s.revalidating[mergedKey] {
		s.revalidatingMu.Unlock()
		return
	}
	s.revalidating[mergedKey] = true
	s.revalidatingMu.Unlock()

	defer func() {
		s.revalidatingMu.Lock()
		delete(s.revalidating, mergedKey)
		s.revalidatingMu.Unlock()
	}()

	agents := s.agentCache.ListActiveWithInfo()
	if len(agents) == 0 {
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	_, err := s.fetchAllInternal(ctx, path, params, agents)
	if err != nil {
		slog.Warn("Background revalidate failed", "path", path, "error", err)
	} else {
		slog.Debug("Background revalidate done", "path", path)
	}
}

// ── Evict expired cache entries (match C++ evict_expired_cache) ──

func (s *ProxyService) evictExpiredCache() {
	now := time.Now()

	// Evict per-agent cache
	s.dataCacheMu.Lock()
	for key, entry := range s.dataCache {
		if now.Sub(entry.createdAt) > cacheStaleTTL {
			delete(s.dataCache, key)
		}
	}
	s.dataCacheMu.Unlock()

	// Evict merged cache
	s.mergedCacheMu.Lock()
	for key, entry := range s.mergedCache {
		if now.Sub(entry.createdAt) > cacheStaleTTL {
			delete(s.mergedCache, key)
		}
	}

	// Cap memory
	for len(s.mergedCache) > maxMergedCacheItems {
		var oldestKey string
		var oldestTime time.Time
		for key, entry := range s.mergedCache {
			if oldestKey == "" || entry.createdAt.Before(oldestTime) {
				oldestKey = key
				oldestTime = entry.createdAt
			}
		}
		if oldestKey != "" {
			delete(s.mergedCache, oldestKey)
		} else {
			break
		}
	}
	s.mergedCacheMu.Unlock()
}

// mergeTotalDataField cộng dồn 1 field vào totalData map.
// Nếu giá trị là số (int/float/string số) → cộng. Nếu không → giữ giá trị đầu tiên.
func mergeTotalDataField(dst map[string]interface{}, key string, value interface{}) {
	existing, hasExisting := dst[key]
	if !hasExisting {
		dst[key] = value
		return
	}

	// Cộng dồn giá trị số
	existNum := toFloat64(existing)
	newNum := toFloat64(value)
	if existNum != 0 || newNum != 0 {
		sum := existNum + newNum
		// Nếu cả 2 là string → trả string formatted
		_, existIsStr := existing.(string)
		_, newIsStr := value.(string)
		if existIsStr || newIsStr {
			dst[key] = formatNumber(sum)
		} else {
			dst[key] = sum
		}
		return
	}
	// Không phải số → giữ nguyên giá trị cũ
}

// toFloat64 chuyển interface{} (string/int/float) thành float64.
func toFloat64(v interface{}) float64 {
	switch n := v.(type) {
	case float64:
		return n
	case float32:
		return float64(n)
	case int:
		return float64(n)
	case int64:
		return float64(n)
	case json.Number:
		f, _ := n.Float64()
		return f
	case string:
		f, err := strconv.ParseFloat(n, 64)
		if err != nil {
			return 0
		}
		return f
	default:
		return 0
	}
}

// formatNumber format float64 thành string: integer nếu tròn, 2 decimal nếu không.
func formatNumber(f float64) string {
	if f == float64(int64(f)) {
		return strconv.FormatInt(int64(f), 10)
	}
	return strconv.FormatFloat(f, 'f', 2, 64)
}
