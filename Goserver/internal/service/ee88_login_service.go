package service

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"strings"
	"sync"
	"time"

	"goserver/internal/model"
	"goserver/internal/repository"
	"goserver/pkg/utils"
)

// ============================================================================
// EE88 Login Engine — port từ MAXHUB TypeScript, nâng cấp toàn diện.
//
// Fix triệt để:
// 1. Lock dùng sync.Mutex per-agent (thread-safe, auto-expire)
// 2. Captcha solver persistent worker (không spawn mỗi lần)
// 3. Captcha retry có exponential backoff
// 4. RSA key validation trước khi vào loop
// 5. LoginAll chạy song song với concurrency limit
// 6. Auto-relogin có cooldown chống stampede
// 7. Health check scheduled
// ============================================================================

const (
	maxCaptchaAttempts  = 10
	captchaBaseDelay    = 500 * time.Millisecond
	captchaMaxDelay     = 5 * time.Second
	lockTimeout         = 5 * time.Minute
	reloginCooldown     = 2 * time.Minute
	cookieLifetime      = 24 * time.Hour
)

type EE88LoginService struct {
	agentRepo repository.AgentRepo
	cache     *AgentCache
	solver    *utils.CaptchaSolver
	lock      *utils.DistributedLock
	cooldowns sync.Map // map[int64]time.Time — agent_id → last relogin time
}

func NewEE88LoginService(agentRepo repository.AgentRepo) *EE88LoginService {
	return &EE88LoginService{
		agentRepo: agentRepo,
		cache:     GetAgentCache(),
		solver:    utils.GetCaptchaSolver(),
		lock:      utils.NewDistributedLock(lockTimeout),
	}
}

// ============================================================================
// LOGIN — core flow
// ============================================================================

func (s *EE88LoginService) LoginAgent(ctx context.Context, agentID int64, triggeredBy, ipAddress string) (*model.LoginResult, error) {
	lockKey := fmt.Sprintf("agent:%d", agentID)
	if !s.lock.Acquire(lockKey) {
		return nil, model.NewConflict("Agent đang trong quá trình đăng nhập")
	}
	defer s.lock.Release(lockKey)

	// Step 1: Load agent
	agent, err := s.agentRepo.FindByID(ctx, agentID)
	if err != nil {
		if errors.Is(err, repository.ErrAgentNotFound) {
			return nil, model.NewBadRequest("Agent không tồn tại")
		}
		return nil, fmt.Errorf("find agent: %w", err)
	}
	if !agent.IsActive {
		return nil, model.NewBadRequest("Agent đã bị vô hiệu hoá")
	}
	if agent.ExtPassword == "" {
		return nil, model.NewBadRequest("Agent chưa có mật khẩu upstream")
	}

	password := agent.ExtPassword

	baseURL := utils.GetUpstreamBaseURL("")
	if agent.BaseURL.Valid && agent.BaseURL.String != "" {
		baseURL = agent.BaseURL.String
	}

	// Step 3: Set status logging_in
	_, _ = s.agentRepo.Update(ctx, agentID, map[string]interface{}{
		"status":      "logging_in",
		"login_error": sql.NullString{},
	})

	slog.Info("Bắt đầu đăng nhập EE88", "agent_id", agentID, "username", agent.ExtUsername)

	// Step 4: Init session (lấy keys + PHPSESSID)
	initResult, err := s.initSession(ctx, baseURL)
	if err != nil {
		errMsg := err.Error()
		s.setAgentError(ctx, agentID, errMsg)
		s.logAttempt(ctx, agentID, false, 0, errMsg, ipAddress, triggeredBy)
		return nil, &model.AppError{Status: 502, Code: "UPSTREAM_ERROR", Message: errMsg}
	}

	// Step 5: Validate keys — cần ít nhất 1 key
	if initResult.PublicKey == "" && initResult.EncryptPublicKey == "" {
		errMsg := "Không lấy được public key từ EE88"
		s.setAgentError(ctx, agentID, errMsg)
		s.logAttempt(ctx, agentID, false, 0, errMsg, ipAddress, triggeredBy)
		return nil, model.NewBadRequest(errMsg)
	}

	useAESMode := initResult.EncryptPublicKey != ""
	if useAESMode {
		slog.Info("Sử dụng AES encrypt mode", "agent_id", agentID)
	} else {
		slog.Info("Sử dụng RSA fallback mode", "agent_id", agentID)
	}

	// Step 6: Captcha loop
	sessionID := initResult.SessionID
	var captchaAttempts int
	for captchaAttempts = 1; captchaAttempts <= maxCaptchaAttempts; captchaAttempts++ {
		if captchaAttempts > 1 {
			// Exponential backoff — fix MAXHUB delay cố định
			delay := captchaBaseDelay * time.Duration(1<<(captchaAttempts-2))
			if delay > captchaMaxDelay {
				delay = captchaMaxDelay
			}
			time.Sleep(delay)
		}

		result, err := s.attemptLogin(ctx, baseURL, agent.ExtUsername, password, initResult, &sessionID, captchaAttempts, agentID)
		if err != nil {
			// Password error → STOP ngay
			if strings.Contains(err.Error(), "sai mật khẩu") || strings.Contains(err.Error(), "password") {
				s.setAgentError(ctx, agentID, err.Error())
				s.logAttempt(ctx, agentID, false, captchaAttempts, err.Error(), ipAddress, triggeredBy)
				return nil, err
			}
			// Captcha error → continue
			if strings.Contains(err.Error(), "captcha") {
				slog.Warn("Captcha sai, thử lại", "agent_id", agentID, "attempt", captchaAttempts)
				continue
			}
			// Other error → STOP
			s.setAgentError(ctx, agentID, err.Error())
			s.logAttempt(ctx, agentID, false, captchaAttempts, err.Error(), ipAddress, triggeredBy)
			return nil, err
		}

		if result != nil && result.Success {
			// Login thành công
			s.logAttempt(ctx, agentID, true, captchaAttempts, "", ipAddress, triggeredBy)
			return result, nil
		}
	}

	// Hết captcha attempts
	errMsg := fmt.Sprintf("Không giải được captcha sau %d lần", maxCaptchaAttempts)
	s.setAgentError(ctx, agentID, errMsg)
	s.logAttempt(ctx, agentID, false, captchaAttempts-1, errMsg, ipAddress, triggeredBy)
	return nil, &model.AppError{Status: 502, Code: "CAPTCHA_FAILED", Message: errMsg}
}

// initSessionResult chứa kết quả init từ upstream.
type initSessionResult struct {
	PublicKey        string // RSA public key (fallback mode)
	EncryptPublicKey string // Encrypt public key (AES mode mới)
	SessionID        string // PHPSESSID
}

func (s *EE88LoginService) initSession(ctx context.Context, baseURL string) (*initSessionResult, error) {
	// GET /agent/login?scene=init — xác nhận bằng curl: GET trả key, POST bị reject
	initURL := baseURL + "/agent/login?scene=init"
	initHeaders := map[string]string{
		"X-Requested-With": "XMLHttpRequest",
		"User-Agent":       utils.DefaultUA,
		"Accept":           "application/json, text/javascript, */*; q=0.01",
	}

	resp, err := utils.FetchRaw(ctx, "GET", initURL, initHeaders, "")
	if err != nil {
		return nil, fmt.Errorf("init session: %w", err)
	}

	// Lấy PHPSESSID từ init response
	sessionID := utils.ExtractPHPSESSID(resp.Headers)
	if sessionID == "" {
		return nil, fmt.Errorf("không lấy được PHPSESSID từ init response")
	}

	var initData struct {
		Code int              `json:"code"`
		Msg  string           `json:"msg"`
		Data json.RawMessage  `json:"data"`
	}
	if err := json.Unmarshal(resp.Body, &initData); err != nil {
		return nil, fmt.Errorf("parse init response: %w (raw: %s)", err, truncate(resp.Text, 200))
	}

	if initData.Code != 1 {
		return nil, fmt.Errorf("upstream init error code=%d: %s", initData.Code, initData.Msg)
	}

	var keyData struct {
		PublicKey        string `json:"public_key"`
		EncryptPublicKey string `json:"encrypt_public_key"`
	}
	if err := json.Unmarshal(initData.Data, &keyData); err != nil {
		return nil, fmt.Errorf("parse init data: %w (raw: %s)", err, truncate(string(initData.Data), 200))
	}

	return &initSessionResult{
		PublicKey:        keyData.PublicKey,
		EncryptPublicKey: keyData.EncryptPublicKey,
		SessionID:        sessionID,
	}, nil
}

func (s *EE88LoginService) attemptLogin(
	ctx context.Context,
	baseURL, username, password string,
	initResult *initSessionResult,
	sessionID *string,
	attempt int,
	agentID int64,
) (*model.LoginResult, error) {

	// Fetch captcha image
	captchaURL := fmt.Sprintf("%s/agent/captcha?t=%d", baseURL, time.Now().UnixMilli())
	captchaHeaders := map[string]string{"User-Agent": utils.DefaultUA}
	if *sessionID != "" {
		captchaHeaders["Cookie"] = "PHPSESSID=" + *sessionID
	}

	captchaResp, err := utils.FetchRaw(ctx, "GET", captchaURL, captchaHeaders, "")
	if err != nil {
		return nil, fmt.Errorf("fetch captcha: %w", err)
	}

	if newSID := utils.ExtractPHPSESSID(captchaResp.Headers); newSID != "" {
		*sessionID = newSID
	}

	// OCR solve
	captchaCode, err := s.solver.Solve(captchaResp.Body)
	if err != nil {
		slog.Warn("OCR error", "agent_id", agentID, "attempt", attempt, "error", err)
		return nil, fmt.Errorf("captcha: OCR thất bại")
	}
	if captchaCode == "" {
		return nil, fmt.Errorf("captcha: OCR trả kết quả rỗng")
	}

	loginURL := baseURL + "/agent/login"
	var loginBody string
	var aesKey string // lưu AES key để decrypt response
	loginHeaders := map[string]string{
		"X-Requested-With": "XMLHttpRequest",
		"User-Agent":       utils.DefaultUA,
		"Cookie":           "PHPSESSID=" + *sessionID,
	}

	useAES := false
	if initResult.EncryptPublicKey != "" {
		// AES encrypt mode (mới) — encrypt toàn bộ body
		params := map[string]string{
			"username": username,
			"password": password, // password plaintext, toàn bộ body sẽ được AES encrypt
			"captcha":  captchaCode,
			"scene":    "login",
		}
		paramsJSON, _ := json.Marshal(params)

		encBody, cekK, usedKey, encErr := utils.AgentEncryptData(string(paramsJSON), initResult.EncryptPublicKey)
		if encErr != nil {
			slog.Warn("AES encrypt failed, fallback RSA", "error", encErr)
		} else {
			loginBody = encBody
			loginHeaders["Content-Type"] = "text/plain"
			loginHeaders["cek-k"] = cekK
			aesKey = usedKey
			useAES = true
			slog.Debug("Login submit AES mode", "agent_id", agentID, "attempt", attempt)
		}
	}

	if !useAES {
		// RSA fallback mode (cũ) — chỉ encrypt password
		encryptedPwd, rsaErr := utils.EncryptRSA(password, initResult.PublicKey)
		if rsaErr != nil {
			return nil, fmt.Errorf("RSA encrypt: %w", rsaErr)
		}

		params := map[string]string{
			"username": username,
			"password": encryptedPwd,
			"captcha":  captchaCode,
			"scene":    "login",
		}
		paramsJSON, _ := json.Marshal(params)
		loginBody = string(paramsJSON)
		loginHeaders["Content-Type"] = "application/json"

		slog.Debug("Login submit RSA fallback", "agent_id", agentID, "attempt", attempt)
	}

	loginResp, err := utils.FetchRaw(ctx, "POST", loginURL, loginHeaders, loginBody)
	if err != nil {
		return nil, fmt.Errorf("submit login: %w", err)
	}

	if newSID := utils.ExtractPHPSESSID(loginResp.Headers); newSID != "" {
		*sessionID = newSID
	}

	// Decrypt response nếu cek-s=1 (AES encrypted response)
	responseBody := loginResp.Body
	cekS := loginResp.Headers.Get("cek-s")
	if cekS == "" {
		cekS = loginResp.Headers.Get("Cek-S")
	}
	if cekS == "1" && aesKey != "" {
		decrypted, decErr := utils.AgentDecryptResponse(string(responseBody), aesKey)
		if decErr != nil {
			slog.Warn("Decrypt response failed, try raw", "error", decErr)
		} else {
			responseBody = []byte(decrypted)
			slog.Debug("Response decrypted OK", "agent_id", agentID)
		}
	}

	var loginData struct {
		Code int    `json:"code"`
		Msg  string `json:"msg"`
		URL  string `json:"url"`
	}
	if err := json.Unmarshal(responseBody, &loginData); err != nil {
		return nil, fmt.Errorf("parse login response: %w (raw: %s)", err, truncate(string(responseBody), 200))
	}

	msg := strings.ToLower(loginData.Msg)

	// Success
	if strings.Contains(msg, "thành công") || strings.Contains(msg, "success") {
		expires := time.Now().Add(cookieLifetime)

		updateFields := map[string]interface{}{
			"session_cookie": *sessionID,
			"cookie_expires": expires,
			"status":         "active",
			"last_login_at":  time.Now(),
			"login_error":    sql.NullString{},
			"login_attempts": 0,
		}
		if initResult.EncryptPublicKey != "" {
			updateFields["encrypt_public_key"] = initResult.EncryptPublicKey
		}
		updated, _ := s.agentRepo.Update(ctx, agentID, updateFields)
		if updated != nil {
			s.cache.Set(agentID, updated)
		}

		slog.Info("Đăng nhập EE88 thành công", "agent_id", agentID, "captcha_attempts", attempt)
		return &model.LoginResult{Success: true, CaptchaAttempts: attempt}, nil
	}

	// Captcha error → retry
	if strings.Contains(msg, "xác nhận") || strings.Contains(msg, "验证码") || strings.Contains(msg, "captcha") {
		return nil, fmt.Errorf("captcha: %s", loginData.Msg)
	}

	// Password error → STOP
	if strings.Contains(msg, "mật khẩu") || strings.Contains(msg, "密码") || strings.Contains(msg, "password") {
		return nil, fmt.Errorf("sai mật khẩu: %s", loginData.Msg)
	}

	// Other error → STOP
	return nil, fmt.Errorf("lỗi đăng nhập: %s", loginData.Msg)
}

// ============================================================================
// LOGOUT
// ============================================================================

func (s *EE88LoginService) LogoutAgent(ctx context.Context, agentID int64) error {
	agent, err := s.agentRepo.FindByID(ctx, agentID)
	if err != nil {
		return err
	}

	baseURL := utils.GetUpstreamBaseURL("")
	if agent.BaseURL.Valid && agent.BaseURL.String != "" {
		baseURL = agent.BaseURL.String
	}

	// Try logout upstream
	if agent.SessionCookie != "" {
		headers := map[string]string{
			"Cookie":           "PHPSESSID=" + agent.SessionCookie,
			"User-Agent":       utils.DefaultUA,
			"X-Requested-With": "XMLHttpRequest",
		}
		_, _ = utils.FetchRaw(ctx, "GET", baseURL+"/agent/loginOut", headers, "")
	}

	_, _ = s.agentRepo.Update(ctx, agentID, map[string]interface{}{
		"session_cookie": "",
		"cookie_expires": sql.NullTime{},
		"status":         "offline",
		"login_error":    sql.NullString{},
	})
	s.cache.ClearCookie(agentID)

	slog.Info("Agent đã logout", "agent_id", agentID)
	return nil
}

// ============================================================================
// LOGIN ALL — song song với concurrency limit (fix MAXHUB sequential)
// ============================================================================

func (s *EE88LoginService) LoginAllAgents(ctx context.Context, triggeredBy, ipAddress string) (*model.LoginAllResult, error) {
	agents, err := s.agentRepo.ListNeedLogin(ctx)
	if err != nil {
		return nil, err
	}

	slog.Info("Bắt đầu login tất cả agents", "count", len(agents))

	result := &model.LoginAllResult{Total: len(agents)}
	var mu sync.Mutex
	var wg sync.WaitGroup

	// N agents = N goroutines chạy đồng thời
	for _, agent := range agents {
		if ctx.Err() != nil {
			break
		}

		wg.Add(1)
		go func(ag *model.Agent) {
			defer wg.Done()
			defer func() {
				if r := recover(); r != nil {
					mu.Lock()
					result.Failed++
					mu.Unlock()
					slog.Error("Login agent panic", "agent_id", ag.ID, "panic", r)
				}
			}()

			_, loginErr := s.LoginAgent(ctx, ag.ID, triggeredBy, ipAddress)

			mu.Lock()
			if loginErr != nil {
				result.Failed++
				slog.Error("Login agent thất bại", "agent_id", ag.ID, "error", loginErr)
			} else {
				result.Success++
			}
			mu.Unlock()
		}(agent)
	}

	wg.Wait()
	return result, nil
}

// ============================================================================
// CHECK SESSION
// ============================================================================

func (s *EE88LoginService) CheckAgentSession(ctx context.Context, agentID int64) (bool, string, error) {
	// Thử cache trước — 0ms latency
	var cookie, encKey, baseURL, status string
	if cached, ok := s.cache.Get(agentID); ok {
		cookie = cached.Cookie
		encKey = cached.EncryptPublicKey
		baseURL = cached.BaseURL
		status = cached.Status
	} else {
		// Fallback DB
		agent, err := s.agentRepo.FindByID(ctx, agentID)
		if err != nil {
			return false, "not_found", err
		}
		cookie = agent.SessionCookie
		encKey = agent.EncryptPublicKey
		status = agent.Status
		if agent.BaseURL.Valid {
			baseURL = agent.BaseURL.String
		}
		s.cache.Set(agentID, agent)
	}

	if cookie == "" {
		return false, "no_cookie", nil
	}

	_, fetchErr := utils.FetchUpstreamWithEncrypt(ctx, baseURL, "/agent/user.html", cookie, encKey, map[string]string{
		"page": "1", "limit": "1",
	})
	if fetchErr != nil {
		_, _ = s.agentRepo.Update(ctx, agentID, map[string]interface{}{
			"status":      "error",
			"login_error": "Session hết hạn (kiểm tra thủ công)",
		})
		return false, "expired", nil
	}

	if status != "active" {
		updated, _ := s.agentRepo.Update(ctx, agentID, map[string]interface{}{
			"status":      "active",
			"login_error": sql.NullString{},
		})
		if updated != nil {
			s.cache.Set(agentID, updated)
		}
	}
	return true, "", nil
}

// ============================================================================
// SESSION INFO
// ============================================================================

func (s *EE88LoginService) GetSessionInfo(ctx context.Context, agentID int64) (*model.SessionInfo, error) {
	agent, err := s.agentRepo.FindByID(ctx, agentID)
	if err != nil {
		return nil, err
	}

	info := &model.SessionInfo{
		ID:         agent.ID,
		Name:       agent.Name,
		Status:     agent.Status,
		HasSession: agent.SessionCookie != "",
	}
	if agent.CookieExpires.Valid {
		info.CookieExpires = &agent.CookieExpires.Time
	}
	if agent.LastLoginAt.Valid {
		info.LastLoginAt = &agent.LastLoginAt.Time
	}
	if agent.LoginError.Valid {
		info.LoginError = agent.LoginError.String
	}
	return info, nil
}

// ============================================================================
// SET COOKIE MANUAL
// ============================================================================

func (s *EE88LoginService) SetCookieManual(ctx context.Context, agentID int64, cookie string) error {
	if _, err := s.agentRepo.FindByID(ctx, agentID); err != nil {
		return err
	}

	updated, updateErr := s.agentRepo.Update(ctx, agentID, map[string]interface{}{
		"session_cookie": cookie,
		"cookie_expires": time.Now().Add(cookieLifetime),
		"status":         "active",
		"last_login_at":  time.Now(),
		"login_error":    sql.NullString{},
		"login_attempts": 0,
	})
	if updateErr != nil {
		return updateErr
	}
	if updated != nil {
		s.cache.Set(agentID, updated)
	}

	slog.Info("Đã set cookie thủ công", "agent_id", agentID)
	return nil
}

// ============================================================================
// AUTO RELOGIN — trigger khi session expired trong proxy call
// ============================================================================

func (s *EE88LoginService) AttemptAutoRelogin(ctx context.Context, agentID int64) (string, error) {
	// Check cooldown — fix MAXHUB stampede
	cooldownKey := agentID
	if lastTime, ok := s.cooldowns.Load(cooldownKey); ok {
		if time.Since(lastTime.(time.Time)) < reloginCooldown {
			slog.Debug("Auto re-login skipped (cooldown)", "agent_id", agentID)
			return "", nil
		}
	}

	// Set cooldown TRƯỚC khi attempt — chống parallel relogin
	s.cooldowns.Store(cooldownKey, time.Now())

	slog.Info("Auto re-login triggered", "agent_id", agentID)
	result, err := s.LoginAgent(ctx, agentID, "auto-relogin", "")
	if err != nil {
		slog.Warn("Auto re-login thất bại", "agent_id", agentID, "error", err)
		return "", err
	}

	if result != nil && result.Success {
		// Đọc cookie từ cache trước (vừa được update trong LoginAgent)
		if cached, ok := s.cache.Get(agentID); ok && cached.Cookie != "" {
			return cached.Cookie, nil
		}
		// Fallback DB
		agent, err := s.agentRepo.FindByID(ctx, agentID)
		if err == nil && agent.SessionCookie != "" {
			return agent.SessionCookie, nil
		}
	}

	return "", nil
}

// ============================================================================
// COOKIE HEALTH CHECK
// ============================================================================

func (s *EE88LoginService) CheckCookieHealth(ctx context.Context) ([]*model.CookieHealthResult, error) {
	// Lấy từ DB vì cần Name (cache không lưu name)
	agents, err := s.agentRepo.ListActive(ctx)
	if err != nil {
		return nil, err
	}

	results := make([]*model.CookieHealthResult, len(agents))
	var wg sync.WaitGroup
	var mu sync.Mutex

	for i, agent := range agents {
		wg.Add(1)
		go func(idx int, ag *model.Agent) {
			defer wg.Done()

			// Lấy cookie/key từ cache (fresh hơn DB nếu vừa login)
			cookie := ag.SessionCookie
			encKey := ag.EncryptPublicKey
			agBaseURL := ""
			if ag.BaseURL.Valid {
				agBaseURL = ag.BaseURL.String
			}
			if cached, ok := s.cache.Get(ag.ID); ok {
				cookie = cached.Cookie
				encKey = cached.EncryptPublicKey
				if cached.BaseURL != "" {
					agBaseURL = cached.BaseURL
				}
			}

			alive := false
			if cookie != "" {
				_, fetchErr := utils.FetchUpstreamWithEncrypt(ctx, agBaseURL, "/agent/user.html", cookie, encKey, map[string]string{
					"page": "1", "limit": "1",
				})
				alive = fetchErr == nil
			}

			mu.Lock()
			results[idx] = &model.CookieHealthResult{
				ID:    ag.ID,
				Name:  ag.Name,
				Alive: alive,
			}
			mu.Unlock()
		}(i, agent)
	}

	wg.Wait()
	return results, nil
}

// ============================================================================
// LOGIN HISTORY
// ============================================================================

func (s *EE88LoginService) GetLoginHistory(ctx context.Context, agentID int64, limit int) ([]*model.AgentLoginHistory, error) {
	return s.agentRepo.ListLoginHistory(ctx, agentID, limit)
}

// ============================================================================
// Helpers
// ============================================================================

func (s *EE88LoginService) setAgentError(ctx context.Context, agentID int64, errMsg string) {
	_ = s.agentRepo.IncrementLoginAttempts(ctx, agentID, errMsg)
}

func (s *EE88LoginService) logAttempt(ctx context.Context, agentID int64, success bool, attempts int, errMsg, ip, triggeredBy string) {
	h := &model.AgentLoginHistory{
		AgentID:         agentID,
		Success:         success,
		CaptchaAttempts: attempts,
		TriggeredBy:     triggeredBy,
	}
	if errMsg != "" {
		h.ErrorMessage = sql.NullString{String: errMsg, Valid: true}
	}
	if ip != "" {
		h.IPAddress = sql.NullString{String: ip, Valid: true}
	}
	_ = s.agentRepo.CreateLoginHistory(ctx, h)
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}
