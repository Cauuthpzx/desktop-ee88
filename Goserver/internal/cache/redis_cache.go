package cache

import (
	"context"
	"log/slog"
	"time"

	"github.com/redis/go-redis/v9"
)

// RedisCache — L2 cache layer giữa memory cache và upstream fetch.
// Nếu Redis không khả dụng, tất cả operations đều graceful degrade (return miss).
type RedisCache struct {
	client     *redis.Client
	defaultTTL time.Duration
	available  bool
}

// NewRedisCache khởi tạo Redis client. Nếu connect thất bại → available=false, ko block server.
func NewRedisCache(redisURL string, defaultTTL time.Duration) *RedisCache {
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		slog.Warn("Redis URL parse failed — L2 cache disabled", "url", redisURL, "error", err)
		return &RedisCache{available: false}
	}

	opts.PoolSize = 20
	opts.MinIdleConns = 5
	opts.DialTimeout = 2 * time.Second
	opts.ReadTimeout = 1 * time.Second
	opts.WriteTimeout = 1 * time.Second

	client := redis.NewClient(opts)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		slog.Warn("Redis ping failed — L2 cache disabled", "error", err)
		return &RedisCache{client: client, available: false}
	}

	slog.Info("Redis L2 cache connected", "url", redisURL, "ttl", defaultTTL)
	return &RedisCache{
		client:     client,
		defaultTTL: defaultTTL,
		available:  true,
	}
}

// Get lấy value từ Redis. Return nil nếu miss hoặc Redis unavailable.
func (c *RedisCache) Get(ctx context.Context, key string) ([]byte, bool) {
	if !c.available {
		return nil, false
	}

	val, err := c.client.Get(ctx, key).Bytes()
	if err != nil {
		if err != redis.Nil {
			slog.Debug("Redis GET error", "key", key, "error", err)
		}
		return nil, false
	}
	return val, true
}

// Set ghi value vào Redis với TTL. Fire-and-forget, không block caller.
func (c *RedisCache) Set(ctx context.Context, key string, value []byte, ttl time.Duration) {
	if !c.available {
		return
	}

	if ttl <= 0 {
		ttl = c.defaultTTL
	}

	if err := c.client.Set(ctx, key, value, ttl).Err(); err != nil {
		slog.Debug("Redis SET error", "key", key, "error", err)
	}
}

// Del xoá key khỏi Redis.
func (c *RedisCache) Del(ctx context.Context, keys ...string) {
	if !c.available || len(keys) == 0 {
		return
	}
	c.client.Del(ctx, keys...)
}

// Available trả true nếu Redis đang connected.
func (c *RedisCache) Available() bool {
	return c.available
}

// Close đóng Redis connection.
func (c *RedisCache) Close() error {
	if c.client != nil {
		return c.client.Close()
	}
	return nil
}
