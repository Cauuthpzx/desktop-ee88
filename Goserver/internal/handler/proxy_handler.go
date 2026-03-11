package handler

import (
	"net/http"
	"strings"
	"time"

	"goserver/internal/service"
)

// ProxyHandler xử lý tất cả upstream proxy requests (bets, reports, deposit/withdrawal).
type ProxyHandler struct {
	proxyService *service.ProxyService
}

func NewProxyHandler(proxyService *service.ProxyService) *ProxyHandler {
	return &ProxyHandler{proxyService: proxyService}
}

// buildDateParams trả start_time, end_time từ query string.
// Nếu client không gửi date, mặc định lấy hôm nay.
func buildDateParams(r *http.Request) (string, string) {
	start := r.URL.Query().Get("start_date")
	end := r.URL.Query().Get("end_date")
	if start == "" {
		today := time.Now().Format("2006-01-02")
		start = today
		end = today
	}
	return start, end
}

// GET /api/proxy/lottery-bets
func (h *ProxyHandler) LotteryBets(w http.ResponseWriter, r *http.Request) {
	startDate, endDate := buildDateParams(r)
	// Upstream params — fetch ALL data (page=1, limit=10000), paginate phía server
	params := map[string]string{
		"es":         "1",
		"start_time": startDate,
		"end_time":   endDate,
		"username":   r.URL.Query().Get("username"),
		"serial_no":  r.URL.Query().Get("serial_no"),
		"lottery_id": r.URL.Query().Get("lottery_id"),
		"play_type":  r.URL.Query().Get("play_type_id"),
		"play_id":    r.URL.Query().Get("play_id"),
		"status":     r.URL.Query().Get("status"),
	}
	cleanEmpty(params)

	result, err := h.proxyService.FetchAll(r.Context(), &service.ProxyParams{
		Path:   "/agent/bet.html",
		Params: params,
		Page:   queryInt(r, "page", 1),
		Limit:  queryInt(r, "limit", 10),
	})
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// GET /api/proxy/provider-bets
func (h *ProxyHandler) ProviderBets(w http.ResponseWriter, r *http.Request) {
	startDate, _ := buildDateParams(r)
	// betOrder.html cần end_date = ngày mai (EE88 convention)
	endDate := r.URL.Query().Get("end_date")
	if endDate == "" {
		endDate = time.Now().Add(24 * time.Hour).Format("2006-01-02")
	}
	params := map[string]string{
		"es":                "1",
		"bet_time":          startDate + " | " + endDate,
		"serial_no":         r.URL.Query().Get("serial_no"),
		"platform_username": r.URL.Query().Get("platform_username"),
	}
	cleanEmpty(params)

	result, err := h.proxyService.FetchAll(r.Context(), &service.ProxyParams{
		Path:   "/agent/betOrder.html",
		Params: params,
		Page:   queryInt(r, "page", 1),
		Limit:  queryInt(r, "limit", 10),
	})
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// GET /api/proxy/lottery-report
func (h *ProxyHandler) LotteryReport(w http.ResponseWriter, r *http.Request) {
	startDate, endDate := buildDateParams(r)
	params := map[string]string{
		"start_time": startDate,
		"end_time":   endDate,
		"lottery_id": r.URL.Query().Get("lottery_id"),
		"username":   r.URL.Query().Get("username"),
	}
	cleanEmpty(params)

	result, err := h.proxyService.FetchAll(r.Context(), &service.ProxyParams{
		Path:   "/agent/reportLottery.html",
		Params: params,
		Page:   queryInt(r, "page", 1),
		Limit:  queryInt(r, "limit", 10),
	})
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// GET /api/proxy/provider-report
func (h *ProxyHandler) ProviderReport(w http.ResponseWriter, r *http.Request) {
	startDate, endDate := buildDateParams(r)
	params := map[string]string{
		"start_time":  startDate,
		"end_time":    endDate,
		"username":    r.URL.Query().Get("username"),
		"platform_id": r.URL.Query().Get("platform_id"),
	}
	cleanEmpty(params)

	result, err := h.proxyService.FetchAll(r.Context(), &service.ProxyParams{
		Path:   "/agent/reportThirdGame.html",
		Params: params,
		Page:   queryInt(r, "page", 1),
		Limit:  queryInt(r, "limit", 10),
	})
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// GET /api/proxy/transaction-log
func (h *ProxyHandler) TransactionLog(w http.ResponseWriter, r *http.Request) {
	startDate, endDate := buildDateParams(r)
	params := map[string]string{
		"start_time": startDate,
		"end_time":   endDate,
		"username":   r.URL.Query().Get("username"),
	}
	cleanEmpty(params)

	result, err := h.proxyService.FetchAll(r.Context(), &service.ProxyParams{
		Path:   "/agent/reportFunds.html",
		Params: params,
		Page:   queryInt(r, "page", 1),
		Limit:  queryInt(r, "limit", 10),
	})
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// GET /api/proxy/deposit-history
func (h *ProxyHandler) DepositHistory(w http.ResponseWriter, r *http.Request) {
	startDate, endDate := buildDateParams(r)
	params := map[string]string{
		"start_time": startDate,
		"end_time":   endDate,
		"username":   r.URL.Query().Get("username"),
		"type":       r.URL.Query().Get("type"),
		"status":     r.URL.Query().Get("status"),
	}
	cleanEmpty(params)

	result, err := h.proxyService.FetchAll(r.Context(), &service.ProxyParams{
		Path:   "/agent/depositAndWithdrawal.html",
		Params: params,
		Page:   queryInt(r, "page", 1),
		Limit:  queryInt(r, "limit", 10),
	})
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// GET /api/proxy/withdrawal-history
func (h *ProxyHandler) WithdrawalHistory(w http.ResponseWriter, r *http.Request) {
	startDate, endDate := buildDateParams(r)
	params := map[string]string{
		"start_time": startDate,
		"end_time":   endDate,
		"username":   r.URL.Query().Get("username"),
		"serial_no":  r.URL.Query().Get("serial_no"),
		"status":     r.URL.Query().Get("status"),
		"type":       "2", // withdrawal only
	}
	cleanEmpty(params)

	result, err := h.proxyService.FetchAll(r.Context(), &service.ProxyParams{
		Path:   "/agent/depositAndWithdrawal.html",
		Params: params,
		Page:   queryInt(r, "page", 1),
		Limit:  queryInt(r, "limit", 10),
	})
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// queryStr trả query param hoặc default value.
func queryStr(r *http.Request, key, defaultVal string) string {
	v := r.URL.Query().Get(key)
	if v == "" {
		return defaultVal
	}
	return v
}

// cleanEmpty xoá các key có value rỗng khỏi params.
func cleanEmpty(params map[string]string) {
	for k, v := range params {
		if strings.TrimSpace(v) == "" {
			delete(params, k)
		}
	}
}
