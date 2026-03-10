package handler

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"time"

	"goserver/internal/middleware"
	"goserver/internal/model"
	"goserver/internal/repository"
	"goserver/internal/service"
)

type AuthHandler struct {
	authService *service.AuthService
}

func NewAuthHandler(authService *service.AuthService) *AuthHandler {
	return &AuthHandler{authService: authService}
}

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req model.RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, model.AuthResponse{
			Status:  "error",
			Message: "invalid request body",
		})
		return
	}

	user, token, err := h.authService.Register(r.Context(), &req)
	if err != nil {
		log.Printf("[REGISTER] Failed for '%s': %v", req.Username, err)
		switch {
		case errors.Is(err, service.ErrInvalidUsername):
			writeJSON(w, http.StatusBadRequest, model.AuthResponse{Status: "error", Message: err.Error()})
		case errors.Is(err, service.ErrPasswordTooShort):
			writeJSON(w, http.StatusBadRequest, model.AuthResponse{Status: "error", Message: err.Error()})
		case errors.Is(err, repository.ErrUsernameExists):
			writeJSON(w, http.StatusConflict, model.AuthResponse{Status: "error", Message: "username already exists"})
		default:
			writeJSON(w, http.StatusInternalServerError, model.AuthResponse{Status: "error", Message: "internal server error"})
		}
		return
	}

	log.Printf("[REGISTER] OK: user '%s' (ID %d)", user.Username, user.ID)
	writeJSON(w, http.StatusCreated, model.AuthResponse{
		Status: "success",
		Data: &model.AuthData{
			User:  user.ToResponse(),
			Token: token,
		},
	})
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req model.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, model.AuthResponse{
			Status:  "error",
			Message: "invalid request body",
		})
		return
	}

	user, token, sessionCookie, err := h.authService.Login(r.Context(), &req)
	if err != nil {
		log.Printf("[LOGIN] Failed for '%s': %v", req.Username, err)
		if errors.Is(err, service.ErrInvalidCredentials) {
			writeJSON(w, http.StatusUnauthorized, model.AuthResponse{Status: "error", Message: err.Error()})
		} else {
			writeJSON(w, http.StatusInternalServerError, model.AuthResponse{Status: "error", Message: "internal server error"})
		}
		return
	}

	log.Printf("[LOGIN] OK: user '%s' (ID %d)", user.Username, user.ID)
	http.SetCookie(w, &http.Cookie{
		Name:     "session",
		Value:    sessionCookie,
		Path:     "/",
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
		MaxAge:   int((7 * 24 * time.Hour).Seconds()),
	})

	writeJSON(w, http.StatusOK, model.AuthResponse{
		Status: "success",
		Data: &model.AuthData{
			User:  user.ToResponse(),
			Token: token,
		},
	})
}

func (h *AuthHandler) ChangePassword(w http.ResponseWriter, r *http.Request) {
	userID := middleware.GetUserID(r.Context())

	var req model.ChangePasswordRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, model.AuthResponse{
			Status:  "error",
			Message: "invalid request body",
		})
		return
	}

	err := h.authService.ChangePassword(r.Context(), userID, &req)
	if err != nil {
		log.Printf("[CHANGE_PASS] Failed for user %d: %v", userID, err)
		switch {
		case errors.Is(err, service.ErrPasswordTooShort):
			writeJSON(w, http.StatusBadRequest, model.AuthResponse{Status: "error", Message: err.Error()})
		case errors.Is(err, service.ErrSamePassword):
			writeJSON(w, http.StatusBadRequest, model.AuthResponse{Status: "error", Message: err.Error()})
		case errors.Is(err, service.ErrWrongOldPassword):
			writeJSON(w, http.StatusForbidden, model.AuthResponse{Status: "error", Message: err.Error()})
		default:
			writeJSON(w, http.StatusInternalServerError, model.AuthResponse{Status: "error", Message: "internal server error"})
		}
		return
	}

	log.Printf("[CHANGE_PASS] OK: user %d", userID)
	writeJSON(w, http.StatusOK, model.AuthResponse{
		Status:  "success",
		Message: "password changed successfully",
	})
}

func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	userID := middleware.GetUserID(r.Context())
	log.Printf("[LOGOUT] User %d", userID)
	cookie, err := r.Cookie("session")
	if err == nil {
		_ = h.authService.Logout(r.Context(), cookie.Value)
	}

	http.SetCookie(w, &http.Cookie{
		Name:     "session",
		Value:    "",
		Path:     "/",
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
		MaxAge:   -1,
	})

	writeJSON(w, http.StatusOK, model.AuthResponse{
		Status:  "success",
		Message: "logged out successfully",
	})
}

func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}
