package middleware

import (
	"context"
	"log"
	"net/http"
	"strings"

	"goserver/internal/service"
)

type contextKey string

const UserIDKey contextKey = "user_id"

func AuthMiddleware(authService *service.AuthService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var userID int64

			// Try JWT from Authorization header
			authHeader := r.Header.Get("Authorization")
			if strings.HasPrefix(authHeader, "Bearer ") {
				tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
				id, err := authService.ValidateJWT(tokenStr)
				if err == nil {
					userID = id
				}
			}

			// Fallback to session cookie
			if userID == 0 {
				cookie, err := r.Cookie("session")
				if err == nil {
					user, err := authService.FindUserBySession(r.Context(), cookie.Value)
					if err == nil && user != nil {
						userID = user.ID
					}
				}
			}

			if userID == 0 {
				log.Printf("[AUTH] Unauthorized: %s %s from %s", r.Method, r.URL.Path, getIP(r))
				http.Error(w, `{"status":"error","message":"unauthorized"}`, http.StatusUnauthorized)
				return
			}

			ctx := context.WithValue(r.Context(), UserIDKey, userID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func GetUserID(ctx context.Context) int64 {
	id, _ := ctx.Value(UserIDKey).(int64)
	return id
}
