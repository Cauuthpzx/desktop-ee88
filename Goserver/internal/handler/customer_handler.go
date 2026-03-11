package handler

import (
	"net/http"
	"strconv"

	"goserver/internal/model"
	"goserver/internal/service"
)

type CustomerHandler struct {
	customerService *service.CustomerService
}

func NewCustomerHandler(customerService *service.CustomerService) *CustomerHandler {
	return &CustomerHandler{customerService: customerService}
}

// GET /api/customers
func (h *CustomerHandler) ListCustomers(w http.ResponseWriter, r *http.Request) {
	params := &model.CustomerListParams{
		Page:      queryInt(r, "page", 1),
		Limit:     queryInt(r, "limit", 10),
		Username:  r.URL.Query().Get("username"),
		Status:    r.URL.Query().Get("status"),
		SortField: r.URL.Query().Get("sort_field"),
		SortDir:   r.URL.Query().Get("sort_dir"),
	}

	if params.Page < 1 {
		params.Page = 1
	}
	if params.Limit < 1 || params.Limit > 100 {
		params.Limit = 10
	}

	result, err := h.customerService.ListCustomers(r.Context(), params)
	if err != nil {
		agentWriteError(w, err)
		return
	}

	agentWriteJSON(w, http.StatusOK, result)
}

func queryInt(r *http.Request, key string, defaultVal int) int {
	s := r.URL.Query().Get(key)
	if s == "" {
		return defaultVal
	}
	v, err := strconv.Atoi(s)
	if err != nil {
		return defaultVal
	}
	return v
}
