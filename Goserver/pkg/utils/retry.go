package utils

import (
	"log/slog"
	"math"
	"math/rand"
	"time"
)

// RetryConfig cấu hình cho retry với exponential backoff + jitter.
type RetryConfig struct {
	MaxRetries  int
	BaseDelay   time.Duration
	MaxDelay    time.Duration
	Jitter      time.Duration
	ShouldRetry func(error) bool // nil = retry all
}

var DefaultRetryConfig = RetryConfig{
	MaxRetries:  2,
	BaseDelay:   500 * time.Millisecond,
	MaxDelay:    5 * time.Second,
	Jitter:      200 * time.Millisecond,
	ShouldRetry: nil,
}

// WithRetry thực thi fn với retry logic.
// Total attempts = 1 (initial) + MaxRetries.
func WithRetry(fn func() error, cfg RetryConfig) error {
	if cfg.MaxRetries <= 0 {
		cfg.MaxRetries = DefaultRetryConfig.MaxRetries
	}
	if cfg.BaseDelay <= 0 {
		cfg.BaseDelay = DefaultRetryConfig.BaseDelay
	}
	if cfg.MaxDelay <= 0 {
		cfg.MaxDelay = DefaultRetryConfig.MaxDelay
	}

	var lastErr error
	for attempt := 0; attempt <= cfg.MaxRetries; attempt++ {
		lastErr = fn()
		if lastErr == nil {
			return nil
		}

		// Không retry nếu hàm filter nói không
		if cfg.ShouldRetry != nil && !cfg.ShouldRetry(lastErr) {
			return lastErr
		}

		if attempt < cfg.MaxRetries {
			delay := time.Duration(float64(cfg.BaseDelay) * math.Pow(2, float64(attempt)))
			if delay > cfg.MaxDelay {
				delay = cfg.MaxDelay
			}
			if cfg.Jitter > 0 {
				delay += time.Duration(rand.Int63n(int64(cfg.Jitter)))
			}
			slog.Debug("Retry", "attempt", attempt+1, "delay_ms", delay.Milliseconds(), "error", lastErr)
			time.Sleep(delay)
		}
	}
	return lastErr
}
