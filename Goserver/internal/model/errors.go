package model

import "net/http"

// AppError là error chuẩn cho toàn project.
type AppError struct {
	Status  int    `json:"-"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

func (e *AppError) Error() string {
	return e.Message
}

// ErrorResponse là JSON response cho error.
type ErrorResponse struct {
	Status  string `json:"status"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

func NewErrorResponse(code, message string) ErrorResponse {
	return ErrorResponse{
		Status:  "error",
		Code:    code,
		Message: message,
	}
}

// Pre-defined errors
var (
	ErrBadRequest      = &AppError{Status: http.StatusBadRequest, Code: "BAD_REQUEST", Message: "invalid request"}
	ErrUnauthorized    = &AppError{Status: http.StatusUnauthorized, Code: "UNAUTHORIZED", Message: "unauthorized"}
	ErrForbidden       = &AppError{Status: http.StatusForbidden, Code: "FORBIDDEN", Message: "forbidden"}
	ErrNotFound        = &AppError{Status: http.StatusNotFound, Code: "NOT_FOUND", Message: "resource not found"}
	ErrConflict        = &AppError{Status: http.StatusConflict, Code: "CONFLICT", Message: "resource conflict"}
	ErrTooManyRequests = &AppError{Status: http.StatusTooManyRequests, Code: "RATE_LIMITED", Message: "rate limit exceeded"}
	ErrInternal        = &AppError{Status: http.StatusInternalServerError, Code: "INTERNAL_ERROR", Message: "internal server error"}
)

func NewBadRequest(msg string) *AppError {
	return &AppError{Status: http.StatusBadRequest, Code: "BAD_REQUEST", Message: msg}
}

func NewConflict(msg string) *AppError {
	return &AppError{Status: http.StatusConflict, Code: "CONFLICT", Message: msg}
}

func NewUnauthorized(msg string) *AppError {
	return &AppError{Status: http.StatusUnauthorized, Code: "UNAUTHORIZED", Message: msg}
}

func NewForbidden(msg string) *AppError {
	return &AppError{Status: http.StatusForbidden, Code: "FORBIDDEN", Message: msg}
}
