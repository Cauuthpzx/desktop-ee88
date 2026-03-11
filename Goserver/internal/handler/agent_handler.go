package handler

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"strconv"
	"strings"

	"goserver/internal/model"
	"goserver/internal/service"
	"goserver/pkg/utils"
)

type AgentHandler struct {
	agentService *service.AgentService
	loginService *service.EE88LoginService
}

func NewAgentHandler(agentService *service.AgentService, loginService *service.EE88LoginService) *AgentHandler {
	return &AgentHandler{
		agentService: agentService,
		loginService: loginService,
	}
}

// ============================================================================
// AGENT CRUD
// ============================================================================

// GET /api/agents/upstream-info — trả cookie + encrypt_public_key cho Desktop direct fetch.
func (h *AgentHandler) UpstreamInfo(w http.ResponseWriter, r *http.Request) {
	agents, err := h.agentService.ListUpstreamInfo(r.Context())
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"agents": agents})
}

// GET /api/agents
func (h *AgentHandler) ListAgents(w http.ResponseWriter, r *http.Request) {
	agents, err := h.agentService.ListAgents(r.Context())
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"agents": agents})
}

// GET /api/agents/{id}
func (h *AgentHandler) GetAgent(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	agent, err := h.agentService.GetAgent(r.Context(), id)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"agent": agent})
}

// POST /api/agents
func (h *AgentHandler) CreateAgent(w http.ResponseWriter, r *http.Request) {
	var req model.CreateAgentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "Body không hợp lệ"))
		return
	}

	agent, err := h.agentService.CreateAgent(r.Context(), &req)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusCreated, map[string]interface{}{"agent": agent})
}

// PATCH /api/agents/{id}
func (h *AgentHandler) UpdateAgent(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	var req model.UpdateAgentRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "Body không hợp lệ"))
		return
	}

	agent, err := h.agentService.UpdateAgent(r.Context(), id, &req)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"agent": agent})
}

// DELETE /api/agents/{id}
func (h *AgentHandler) DeleteAgent(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	mode := r.URL.Query().Get("mode")
	if mode == "destroy" {
		err = h.agentService.DeleteAgent(r.Context(), id)
	} else {
		err = h.agentService.DeactivateAgent(r.Context(), id)
	}

	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"status": "ok"})
}

// ============================================================================
// EE88 AUTH
// ============================================================================

// POST /api/ee88-auth/{id}/login
func (h *AgentHandler) LoginAgent(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	ip := utils.GetIPAddress(r)
	result, err := h.loginService.LoginAgent(r.Context(), id, "manual", ip)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// POST /api/ee88-auth/{id}/logout
func (h *AgentHandler) LogoutAgent(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	if err := h.loginService.LogoutAgent(r.Context(), id); err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"status": "ok"})
}

// POST /api/ee88-auth/login-all
func (h *AgentHandler) LoginAllAgents(w http.ResponseWriter, r *http.Request) {
	ip := utils.GetIPAddress(r)
	result, err := h.loginService.LoginAllAgents(r.Context(), "manual", ip)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, result)
}

// POST /api/ee88-auth/{id}/check
func (h *AgentHandler) CheckAgentSession(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	valid, reason, err := h.loginService.CheckAgentSession(r.Context(), id)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{
		"valid":  valid,
		"reason": reason,
	})
}

// GET /api/ee88-auth/{id}/session
func (h *AgentHandler) GetSessionInfo(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	info, err := h.loginService.GetSessionInfo(r.Context(), id)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, info)
}

// PATCH /api/ee88-auth/{id}/cookie
func (h *AgentHandler) SetCookieManual(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	var req model.SetCookieRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Cookie == "" {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "Cookie không được trống"))
		return
	}

	if err := h.loginService.SetCookieManual(r.Context(), id, req.Cookie); err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"status": "ok"})
}

// GET /api/ee88-auth/{id}/login-history
func (h *AgentHandler) GetLoginHistory(w http.ResponseWriter, r *http.Request) {
	id, err := parseAgentID(r)
	if err != nil {
		agentWriteJSON(w, http.StatusBadRequest, model.NewErrorResponse("BAD_REQUEST", "ID không hợp lệ"))
		return
	}

	limit := 20
	if l := r.URL.Query().Get("limit"); l != "" {
		if parsed, err := strconv.Atoi(l); err == nil && parsed > 0 && parsed <= 100 {
			limit = parsed
		}
	}

	history, err := h.loginService.GetLoginHistory(r.Context(), id, limit)
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"history": history})
}

// GET /api/agents/cookie-health
func (h *AgentHandler) CookieHealth(w http.ResponseWriter, r *http.Request) {
	results, err := h.loginService.CheckCookieHealth(r.Context())
	if err != nil {
		agentWriteError(w, err)
		return
	}
	agentWriteJSON(w, http.StatusOK, map[string]interface{}{"results": results})
}

// ============================================================================
// Helpers
// ============================================================================

func parseAgentID(r *http.Request) (int64, error) {
	// Extract ID from URL path
	// Pattern: /api/agents/{id} or /api/ee88-auth/{id}/action
	path := r.URL.Path
	parts := strings.Split(strings.Trim(path, "/"), "/")

	for i, p := range parts {
		if (p == "agents" || p == "ee88-auth") && i+1 < len(parts) {
			idStr := parts[i+1]
			// Skip non-numeric segments like "cookie-health" or "login-all"
			id, err := strconv.ParseInt(idStr, 10, 64)
			if err != nil {
				continue
			}
			return id, nil
		}
	}
	return 0, model.NewBadRequest("missing agent ID")
}

func agentWriteJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(data); err != nil {
		slog.Error("writeJSON encode failed", "error", err)
	}
}

func agentWriteError(w http.ResponseWriter, err error) {
	if appErr, ok := err.(*model.AppError); ok {
		agentWriteJSON(w, appErr.Status, model.NewErrorResponse(appErr.Code, appErr.Message))
		return
	}
	slog.Error("Unhandled error", "error", err)
	agentWriteJSON(w, http.StatusInternalServerError, model.NewErrorResponse("INTERNAL_ERROR", "Lỗi hệ thống"))
}
