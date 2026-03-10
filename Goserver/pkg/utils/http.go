package utils

import (
	"fmt"
	"log"
	"net/http"
	"runtime/debug"
	"strings"
)

// HTTPError is an error with an HTTP status code.
type HTTPError interface {
	Error() string
	StatusCode() int
}

type httpError struct {
	status  int
	message string
}

func (h httpError) Error() string {
	return h.message
}

func (h httpError) StatusCode() int {
	return h.status
}

// HTTPPanic panics with an HTTPError, expected to be recovered by RecoverErrors middleware.
func HTTPPanic(status int, fmtStr string, args ...interface{}) {
	panic(httpError{status, fmt.Sprintf(fmtStr, args...)})
}

// CORS wraps an HTTP handler, adding appropriate CORS headers.
func CORS(fn http.Handler) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if origin := r.Header.Get("Origin"); origin != "" {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
			w.Header().Set("Access-Control-Allow-Credentials", "true")
			w.Header().Set("Access-Control-Allow-Headers",
				"Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization")
			w.Header().Set("Access-Control-Expose-Headers", "Status, Content-Type, Content-Length")
		}
		if r.Method == "OPTIONS" {
			return
		}
		fn.ServeHTTP(w, r)
	}
}

// RecoverErrors recovers panics in HTTP handlers, logs the stack trace,
// and returns the appropriate HTTP error response.
func RecoverErrors(fn http.Handler) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if thing := recover(); thing != nil {
				code := http.StatusInternalServerError
				status := "Internal server error"
				switch v := thing.(type) {
				case HTTPError:
					code = v.StatusCode()
					status = v.Error()
				default:
					status = fmt.Sprintf("%v", thing)
					log.Printf("%v", thing)
					log.Println(string(debug.Stack()))
				}
				http.Error(w, fmt.Sprintf(`{"status":"error","message":"%s"}`, status), code)
			}
		}()
		fn.ServeHTTP(w, r)
	}
}

// GetHost returns the host of the request, taking into account X-Forwarded-Host headers.
func GetHost(r *http.Request) string {
	if h := r.Header.Get("X-Forwarded-Host"); h != "" {
		return h
	}
	return r.Host
}

// GetIPAddress returns the IP address of the request, taking into account X-Forwarded-For headers.
func GetIPAddress(r *http.Request) string {
	ipAddress := r.RemoteAddr
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		ipAddress = xff
	}
	if colon := strings.LastIndex(ipAddress, ":"); colon >= 0 {
		ipAddress = ipAddress[:colon]
	}
	return ipAddress
}

// IsRequestSecure checks if the request was made over HTTPS.
func IsRequestSecure(r *http.Request) bool {
	if r.TLS != nil {
		return true
	}
	return r.Header.Get("X-Forwarded-Proto") == "https"
}
