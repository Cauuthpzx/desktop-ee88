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
// AgentCache — memory cache cho agent session data.
// Latency: ~0ms (vs 1-3ms query DB).
// Thread-safe: sync.RWMutex cho concurrent read, exclusive write.
// Load từ DB on startup, update on login/logout/set-cookie.
// ============================================================================

type CachedAgent struct {
	Cookie           string
	EncryptPublicKey string
	BaseURL          string // empty = dùng default
	CookieExpires    time.Time
	Status           string
}

type AgentCache struct {
	mu    sync.RWMutex
	items map[int64]*CachedAgent
}

var (
	globalCache     *AgentCache
	globalCacheOnce sync.Once
)

func GetAgentCache() *AgentCache {
	globalCacheOnce.Do(func() {
		globalCache = &AgentCache{
			items: make(map[int64]*CachedAgent),
		}
	})
	return globalCache
}

// LoadFromDB tải toàn bộ agents active từ DB vào cache. Gọi 1 lần khi server start.
func (c *AgentCache) LoadFromDB(ctx context.Context, agentRepo repository.AgentRepo) error {
	agents, err := agentRepo.ListAll(ctx)
	if err != nil {
		return err
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	for _, ag := range agents {
		c.items[ag.ID] = agentToCached(ag)
	}

	slog.Info("AgentCache loaded", "count", len(c.items))
	return nil
}

// Get trả cached agent data. ok=false nếu không có trong cache.
func (c *AgentCache) Get(agentID int64) (*CachedAgent, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	item, ok := c.items[agentID]
	if !ok {
		return nil, false
	}
	// Trả copy để tránh race
	cp := *item
	return &cp, true
}

// Set cập nhật cache cho 1 agent.
func (c *AgentCache) Set(agentID int64, agent *model.Agent) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.items[agentID] = agentToCached(agent)
}

// SetFields cập nhật từng field mà không cần full agent struct.
func (c *AgentCache) SetFields(agentID int64, cookie, encryptPublicKey, baseURL, status string, expires time.Time) {
	c.mu.Lock()
	defer c.mu.Unlock()

	item, ok := c.items[agentID]
	if !ok {
		item = &CachedAgent{}
		c.items[agentID] = item
	}
	item.Cookie = cookie
	item.EncryptPublicKey = encryptPublicKey
	item.BaseURL = baseURL
	item.Status = status
	item.CookieExpires = expires
}

// UpdateCookie chỉ cập nhật cookie + expires + status.
func (c *AgentCache) UpdateCookie(agentID int64, cookie string, expires time.Time) {
	c.mu.Lock()
	defer c.mu.Unlock()

	item, ok := c.items[agentID]
	if !ok {
		item = &CachedAgent{}
		c.items[agentID] = item
	}
	item.Cookie = cookie
	item.CookieExpires = expires
	if cookie != "" {
		item.Status = "active"
	} else {
		item.Status = "offline"
	}
}

// UpdateEncryptKey cập nhật encrypt_public_key.
func (c *AgentCache) UpdateEncryptKey(agentID int64, key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if item, ok := c.items[agentID]; ok {
		item.EncryptPublicKey = key
	}
}

// Delete xoá agent khỏi cache.
func (c *AgentCache) Delete(agentID int64) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.items, agentID)
}

// ClearCookie xoá cookie (logout).
func (c *AgentCache) ClearCookie(agentID int64) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if item, ok := c.items[agentID]; ok {
		item.Cookie = ""
		item.EncryptPublicKey = ""
		item.CookieExpires = time.Time{}
		item.Status = "offline"
	}
}

// ListActive trả danh sách agentID có cookie hợp lệ.
func (c *AgentCache) ListActive() []int64 {
	c.mu.RLock()
	defer c.mu.RUnlock()

	var ids []int64
	for id, item := range c.items {
		if item.Cookie != "" && item.Status == "active" {
			ids = append(ids, id)
		}
	}
	return ids
}

func agentToCached(ag *model.Agent) *CachedAgent {
	cached := &CachedAgent{
		Cookie:           ag.SessionCookie,
		EncryptPublicKey: ag.EncryptPublicKey,
		Status:           ag.Status,
	}
	if ag.BaseURL.Valid {
		cached.BaseURL = ag.BaseURL.String
	}
	if ag.CookieExpires.Valid {
		cached.CookieExpires = ag.CookieExpires.Time
	}
	return cached
}
