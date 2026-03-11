package middleware

import (
	"net/http"
	"slices"
)

// CORS middleware kiểm tra origin có trong whitelist không.
// Nếu AllowedOrigins rỗng, cho phép tất cả (dev mode).
func CORS(allowedOrigins []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")
			if origin != "" {
				if len(allowedOrigins) == 0 || slices.Contains(allowedOrigins, origin) {
					w.Header().Set("Access-Control-Allow-Origin", origin)
					w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, PATCH, DELETE")
					w.Header().Set("Access-Control-Allow-Credentials", "true")
					w.Header().Set("Access-Control-Allow-Headers",
						"Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization")
					w.Header().Set("Access-Control-Expose-Headers", "Status, Content-Type, Content-Length")
					w.Header().Set("Access-Control-Max-Age", "3600")
				}
			}
			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusNoContent)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
