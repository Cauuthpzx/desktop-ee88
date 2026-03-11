package utils

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"
)

// ============================================================================
// Upstream HTTP client — giao tiếp với EE88.
// Circuit breaker + retry + session expiry detection.
// Fix MAXHUB: connection pooling via Go http.Client (mặc định đã có).
// ============================================================================

const (
	UpstreamTimeout = 2 * time.Minute
	DefaultUA       = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

var (
	ErrSessionExpired = errors.New("AGENT_SESSION_EXPIRED")
	ErrUpstreamError  = errors.New("UPSTREAM_ERROR")
	ErrUpstreamTimeout = errors.New("UPSTREAM_TIMEOUT")
)

// upstreamClient dùng connection pooling.
var upstreamClient = &http.Client{
	Timeout: UpstreamTimeout,
	Transport: &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 50,
		IdleConnTimeout:     60 * time.Second,
		DisableKeepAlives:   false,
	},
	// Không follow redirect — detect session expiry qua 301/302.
	CheckRedirect: func(req *http.Request, via []*http.Request) error {
		return http.ErrUseLastResponse
	},
}

// Per-agent circuit breaker — 1 agent fail không ảnh hưởng agent khác.
var (
	agentBreakers   = make(map[string]*CircuitBreaker)
	agentBreakersMu sync.Mutex
)

func getAgentBreaker(cookie string) *CircuitBreaker {
	// Dùng 8 ký tự đầu cookie làm key (đủ unique, tránh leak)
	key := cookie
	if len(key) > 8 {
		key = key[:8]
	}

	agentBreakersMu.Lock()
	defer agentBreakersMu.Unlock()

	if cb, ok := agentBreakers[key]; ok {
		return cb
	}

	cb := NewCircuitBreaker(CircuitBreakerConfig{
		Name:             "upstream:" + key,
		FailureThreshold: 5,
		ResetTimeout:     30 * time.Second,
		SuccessThreshold: 2,
		ShouldCountFailure: func(err error) bool {
			// Session expired / tham số sai = credential issue, KHÔNG phải infra failure
			return !errors.Is(err, ErrSessionExpired)
		},
	})
	agentBreakers[key] = cb
	return cb
}

type UpstreamResponse struct {
	Code      int                    `json:"code"`
	Msg       string                 `json:"msg,omitempty"`
	Data      json.RawMessage        `json:"data,omitempty"`
	Count     int                    `json:"count,omitempty"`
	TotalData map[string]interface{} `json:"total_data,omitempty"`
}

func GetUpstreamBaseURL(agentBaseURL string) string {
	if agentBaseURL != "" {
		return agentBaseURL
	}
	base := os.Getenv("UPSTREAM_BASE_URL")
	if base == "" {
		base = "https://a2u4k.ee88dly.com"
	}
	return base
}

// FetchUpstream gọi upstream với circuit breaker + retry.
func FetchUpstream(ctx context.Context, path, cookie string, params map[string]string) (*UpstreamResponse, error) {
	return FetchUpstreamWithEncrypt(ctx, "", path, cookie, "", params)
}

// FetchUpstreamWithEncrypt gọi upstream với AES encrypt mode nếu có encryptPublicKey.
func FetchUpstreamWithEncrypt(ctx context.Context, baseURL, path, cookie, encryptPublicKey string, params map[string]string) (*UpstreamResponse, error) {
	var result *UpstreamResponse
	breaker := getAgentBreaker(cookie)
	err := breaker.Execute(func() error {
		return WithRetry(func() error {
			var fetchErr error
			result, fetchErr = fetchUpstreamOnce2(ctx, baseURL, path, cookie, encryptPublicKey, params)
			return fetchErr
		}, RetryConfig{
			MaxRetries: 2,
			ShouldRetry: func(err error) bool {
				return !errors.Is(err, ErrSessionExpired)
			},
		})
	})
	return result, err
}

func fetchUpstreamOnce(ctx context.Context, path, cookie string, params map[string]string) (*UpstreamResponse, error) {
	return fetchUpstreamOnce2(ctx, "", path, cookie, "", params)
}

func fetchUpstreamOnce2(ctx context.Context, agentBaseURL, path, cookie, encryptPublicKey string, params map[string]string) (*UpstreamResponse, error) {
	baseURL := GetUpstreamBaseURL(agentBaseURL)
	fullURL := baseURL + path

	var bodyStr string
	var aesKey string
	headers := map[string]string{
		"Cookie":           "PHPSESSID=" + cookie,
		"User-Agent":       DefaultUA,
		"Accept":           "application/json, text/javascript, */*; q=0.01",
		"X-Requested-With": "XMLHttpRequest",
		"Referer":          baseURL,
		"Origin":           baseURL,
	}

	if encryptPublicKey != "" {
		// AES encrypt mode — encrypt params as JSON body
		paramsJSON, _ := json.Marshal(params)
		encBody, cekK, usedKey, encErr := AgentEncryptData(string(paramsJSON), encryptPublicKey)
		if encErr != nil {
			slog.Warn("AES encrypt failed for upstream call, fallback form", "error", encErr, "path", path)
		} else {
			bodyStr = encBody
			aesKey = usedKey
			headers["Content-Type"] = "text/plain"
			headers["cek-k"] = cekK
		}
	}

	if bodyStr == "" {
		// Form-urlencoded fallback
		form := url.Values{}
		for k, v := range params {
			form.Set(k, v)
		}
		bodyStr = form.Encode()
		headers["Content-Type"] = "application/x-www-form-urlencoded"
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, fullURL, strings.NewReader(bodyStr))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := upstreamClient.Do(req)
	if err != nil {
		if ctx.Err() != nil {
			return nil, fmt.Errorf("%w: request cancelled", ErrUpstreamTimeout)
		}
		return nil, fmt.Errorf("%w: %v", ErrUpstreamError, err)
	}
	defer resp.Body.Close()

	// Detect redirect → session expired
	if resp.StatusCode == 301 || resp.StatusCode == 302 {
		location := resp.Header.Get("Location")
		if strings.Contains(location, "login") || strings.Contains(location, "index") {
			return nil, fmt.Errorf("%w: redirect to %s", ErrSessionExpired, location)
		}
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("%w: status %d", ErrUpstreamError, resp.StatusCode)
	}

	body, err := io.ReadAll(io.LimitReader(resp.Body, 10*1024*1024)) // Max 10MB
	if err != nil {
		return nil, fmt.Errorf("%w: read body: %v", ErrUpstreamError, err)
	}

	// Decrypt response nếu cek-s=1 (AES encrypted response)
	cekS := resp.Header.Get("cek-s")
	if cekS == "" {
		cekS = resp.Header.Get("Cek-S")
	}
	if cekS == "1" && aesKey != "" {
		decrypted, decErr := AgentDecryptResponse(string(body), aesKey)
		if decErr != nil {
			slog.Warn("Decrypt upstream response failed", "error", decErr, "path", path)
		} else {
			body = []byte(decrypted)
		}
	}

	// HTML response → session expired
	trimmedBody := strings.TrimSpace(string(body))
	if strings.HasPrefix(trimmedBody, "<!") ||
		strings.HasPrefix(trimmedBody, "<html") ||
		strings.HasPrefix(trimmedBody, "<HTML") ||
		strings.HasPrefix(trimmedBody, "<?xml") ||
		strings.HasPrefix(trimmedBody, "<head") {
		return nil, fmt.Errorf("%w: HTML response", ErrSessionExpired)
	}

	var result UpstreamResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("%w: invalid JSON: %v", ErrUpstreamError, err)
	}

	// Success codes: 0, 1
	if result.Code == 0 || result.Code == 1 {
		msg := strings.ToLower(result.Msg)
		if strings.Contains(msg, "đăng nhập") || strings.Contains(msg, "login") {
			return nil, fmt.Errorf("%w: code %d but login required", ErrSessionExpired, result.Code)
		}
		return &result, nil
	}

	// Code 2 = no data
	if result.Code == 2 {
		slog.Debug("Upstream empty result", "path", path, "code", result.Code)
		result.Data = json.RawMessage("[]")
		result.Count = 0
		return &result, nil
	}

	// Code 302 or msg contains "login" → session expired
	if result.Code == 302 || strings.Contains(strings.ToLower(result.Msg), "login") {
		return nil, fmt.Errorf("%w: code %d", ErrSessionExpired, result.Code)
	}

	slog.Warn("Upstream non-success", "path", path, "code", result.Code, "msg", result.Msg)
	return nil, fmt.Errorf("%w: code %d msg %s", ErrUpstreamError, result.Code, result.Msg)
}

// ============================================================================
// Raw fetch — dùng cho login flow (cần custom headers, binary response).
// ============================================================================

type RawResponse struct {
	StatusCode int
	Headers    http.Header
	Body       []byte
	Text       string
}

// FetchRaw gọi HTTP request thô, trả raw response.
func FetchRaw(ctx context.Context, method, rawURL string, headers map[string]string, body string) (*RawResponse, error) {
	var bodyReader io.Reader
	if body != "" {
		bodyReader = strings.NewReader(body)
	}

	req, err := http.NewRequestWithContext(ctx, method, rawURL, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := upstreamClient.Do(req)
	if err != nil {
		if ctx.Err() != nil {
			return nil, fmt.Errorf("request timeout: %w", err)
		}
		return nil, fmt.Errorf("fetch: %w", err)
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(io.LimitReader(resp.Body, 5*1024*1024)) // Max 5MB
	if err != nil {
		return nil, fmt.Errorf("read body: %w", err)
	}

	return &RawResponse{
		StatusCode: resp.StatusCode,
		Headers:    resp.Header,
		Body:       data,
		Text:       string(data),
	}, nil
}

// ExtractPHPSESSID lấy PHPSESSID từ Set-Cookie header.
func ExtractPHPSESSID(headers http.Header) string {
	for _, cookie := range headers.Values("Set-Cookie") {
		for _, part := range strings.Split(cookie, ";") {
			part = strings.TrimSpace(part)
			if strings.HasPrefix(part, "PHPSESSID=") {
				return strings.TrimPrefix(part, "PHPSESSID=")
			}
		}
	}
	return ""
}
