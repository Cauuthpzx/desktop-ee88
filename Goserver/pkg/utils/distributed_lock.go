package utils

import (
	"sync"
	"time"
)

// DistributedLock — lock per-key với auto-expire.
// Dùng sync.Map + timestamp, thread-safe.
// Fix lỗi MAXHUB: in-memory Map không atomic.
// Trong single-instance Go server, sync.Map là đủ.
// Nếu scale multi-instance → chuyển sang Redis SETNX.

type lockEntry struct {
	mu        sync.Mutex
	timestamp time.Time
	held      bool
}

type DistributedLock struct {
	locks   sync.Map
	timeout time.Duration
}

func NewDistributedLock(timeout time.Duration) *DistributedLock {
	if timeout <= 0 {
		timeout = 5 * time.Minute
	}
	return &DistributedLock{timeout: timeout}
}

// Acquire trả true nếu lock thành công, false nếu đã bị lock.
func (dl *DistributedLock) Acquire(key string) bool {
	val, _ := dl.locks.LoadOrStore(key, &lockEntry{})
	entry := val.(*lockEntry)

	entry.mu.Lock()
	defer entry.mu.Unlock()

	now := time.Now()

	// Auto-expire: nếu lock quá lâu → force release
	if entry.held && now.Sub(entry.timestamp) >= dl.timeout {
		entry.held = false
	}

	if entry.held {
		return false
	}

	entry.held = true
	entry.timestamp = now
	return true
}

// Release giải phóng lock.
func (dl *DistributedLock) Release(key string) {
	val, ok := dl.locks.Load(key)
	if !ok {
		return
	}
	entry := val.(*lockEntry)
	entry.mu.Lock()
	defer entry.mu.Unlock()
	entry.held = false
}
