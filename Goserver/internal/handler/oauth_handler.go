package handler

import (
	"net/http"
	"net/url"

	"goserver/internal/config"
	"goserver/internal/model"
	"goserver/internal/service"
)

type OAuthHandler struct {
	oauthService *service.OAuthService
	cfg          *config.Config
}

func NewOAuthHandler(oauthService *service.OAuthService, cfg *config.Config) *OAuthHandler {
	return &OAuthHandler{oauthService: oauthService, cfg: cfg}
}

func (h *OAuthHandler) GoogleLogin(w http.ResponseWriter, r *http.Request) {
	state, err := service.GenerateState()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, model.AuthResponse{
			Status: "error", Message: "internal server error",
		})
		return
	}

	http.SetCookie(w, &http.Cookie{
		Name:     "oauth_state",
		Value:    state,
		Path:     "/",
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   300,
	})

	http.Redirect(w, r, h.oauthService.GoogleAuthURL(state), http.StatusTemporaryRedirect)
}

func (h *OAuthHandler) GoogleCallback(w http.ResponseWriter, r *http.Request) {
	if err := h.validateState(r); err != nil {
		h.redirectWithError(w, r, "invalid_state")
		return
	}

	code := r.URL.Query().Get("code")
	if code == "" {
		h.redirectWithError(w, r, "missing_code")
		return
	}

	_, token, err := h.oauthService.HandleGoogleCallback(r.Context(), code)
	if err != nil {
		h.redirectWithError(w, r, "oauth_failed")
		return
	}

	h.redirectWithToken(w, r, token)
}

func (h *OAuthHandler) FacebookLogin(w http.ResponseWriter, r *http.Request) {
	state, err := service.GenerateState()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, model.AuthResponse{
			Status: "error", Message: "internal server error",
		})
		return
	}

	http.SetCookie(w, &http.Cookie{
		Name:     "oauth_state",
		Value:    state,
		Path:     "/",
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   300,
	})

	http.Redirect(w, r, h.oauthService.FacebookAuthURL(state), http.StatusTemporaryRedirect)
}

func (h *OAuthHandler) FacebookCallback(w http.ResponseWriter, r *http.Request) {
	if err := h.validateState(r); err != nil {
		h.redirectWithError(w, r, "invalid_state")
		return
	}

	code := r.URL.Query().Get("code")
	if code == "" {
		h.redirectWithError(w, r, "missing_code")
		return
	}

	_, token, err := h.oauthService.HandleFacebookCallback(r.Context(), code)
	if err != nil {
		h.redirectWithError(w, r, "oauth_failed")
		return
	}

	h.redirectWithToken(w, r, token)
}

func (h *OAuthHandler) validateState(r *http.Request) error {
	stateCookie, err := r.Cookie("oauth_state")
	if err != nil {
		return err
	}

	stateParam := r.URL.Query().Get("state")
	if stateParam != stateCookie.Value {
		return http.ErrNoCookie
	}

	return nil
}

func (h *OAuthHandler) redirectWithToken(w http.ResponseWriter, r *http.Request, token string) {
	redirectURL, _ := url.Parse(h.cfg.FrontendURL)
	redirectURL.Path = "/auth/callback"
	q := redirectURL.Query()
	q.Set("token", token)
	redirectURL.RawQuery = q.Encode()

	// Clear oauth_state cookie
	http.SetCookie(w, &http.Cookie{
		Name:   "oauth_state",
		Value:  "",
		Path:   "/",
		MaxAge: -1,
	})

	http.Redirect(w, r, redirectURL.String(), http.StatusTemporaryRedirect)
}

func (h *OAuthHandler) redirectWithError(w http.ResponseWriter, r *http.Request, errMsg string) {
	redirectURL, _ := url.Parse(h.cfg.FrontendURL)
	redirectURL.Path = "/auth/callback"
	q := redirectURL.Query()
	q.Set("error", errMsg)
	redirectURL.RawQuery = q.Encode()

	http.Redirect(w, r, redirectURL.String(), http.StatusTemporaryRedirect)
}
