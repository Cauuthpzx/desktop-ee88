package utils

import (
	"errors"
	"log/slog"
	"sync"
	"time"
)

// CircuitBreaker bảo vệ upstream khỏi cascading failure.
// States: CLOSED → OPEN → HALF_OPEN → CLOSED.

type CBState int

const (
	CBClosed   CBState = iota
	CBOpen
	CBHalfOpen
)

func (s CBState) String() string {
	switch s {
	case CBClosed:
		return "CLOSED"
	case CBOpen:
		return "OPEN"
	case CBHalfOpen:
		return "HALF_OPEN"
	default:
		return "UNKNOWN"
	}
}

var ErrCircuitOpen = errors.New("circuit breaker đang OPEN — upstream tạm ngưng")

type CircuitBreakerConfig struct {
	Name              string
	FailureThreshold  int
	ResetTimeout      time.Duration
	SuccessThreshold  int
	ShouldCountFailure func(error) bool // nil = count all
}

type CircuitBreaker struct {
	mu               sync.Mutex
	name             string
	state            CBState
	failureCount     int
	successCount     int
	failureThreshold int
	successThreshold int
	resetTimeout     time.Duration
	lastFailure      time.Time
	shouldCount      func(error) bool
}

func NewCircuitBreaker(cfg CircuitBreakerConfig) *CircuitBreaker {
	ft := cfg.FailureThreshold
	if ft <= 0 {
		ft = 5
	}
	st := cfg.SuccessThreshold
	if st <= 0 {
		st = 2
	}
	rt := cfg.ResetTimeout
	if rt <= 0 {
		rt = 30 * time.Second
	}
	sc := cfg.ShouldCountFailure
	if sc == nil {
		sc = func(error) bool { return true }
	}
	return &CircuitBreaker{
		name:             cfg.Name,
		state:            CBClosed,
		failureThreshold: ft,
		successThreshold: st,
		resetTimeout:     rt,
		shouldCount:      sc,
	}
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	switch cb.state {
	case CBOpen:
		if time.Since(cb.lastFailure) >= cb.resetTimeout {
			cb.state = CBHalfOpen
			cb.successCount = 0
			slog.Info("CircuitBreaker HALF_OPEN", "name", cb.name)
		} else {
			cb.mu.Unlock()
			return ErrCircuitOpen
		}
	}
	cb.mu.Unlock()

	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		if cb.shouldCount(err) {
			cb.failureCount++
			cb.lastFailure = time.Now()
			if cb.failureCount >= cb.failureThreshold {
				cb.state = CBOpen
				slog.Warn("CircuitBreaker OPEN", "name", cb.name, "failures", cb.failureCount)
			}
		}
		return err
	}

	// Success
	switch cb.state {
	case CBHalfOpen:
		cb.successCount++
		if cb.successCount >= cb.successThreshold {
			cb.state = CBClosed
			cb.failureCount = 0
			slog.Info("CircuitBreaker CLOSED", "name", cb.name)
		}
	case CBClosed:
		cb.failureCount = 0 // reset on success
	}

	return nil
}
