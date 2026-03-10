package utils

import (
	"net/http"
	"strings"
)

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
