package model

// CustomerListParams — query params từ client cho customer list API.
type CustomerListParams struct {
	Page      int    `json:"page"`
	Limit     int    `json:"limit"`
	Username  string `json:"username"`
	Status    string `json:"status"`     // "", "1" (active), "2" (locked)
	SortField string `json:"sort_field"` // id, username, balance, frozen_amount
	SortDir   string `json:"sort_dir"`   // asc, desc
}

// UpstreamUser — 1 user từ upstream API /agent/user.html.
type UpstreamUser struct {
	ID               int64   `json:"id"`
	Username         string  `json:"username"`
	TypeFormat       string  `json:"type_format"`
	ParentUser       string  `json:"parent_user"`
	Money            string  `json:"money"`
	DepositCount     int     `json:"deposit_count"`
	WithdrawalCount  int     `json:"withdrawal_count"`
	DepositAmount    string  `json:"deposit_amount"`
	WithdrawalAmount string  `json:"withdrawal_amount"`
	LoginTime        string  `json:"login_time"`
	RegisterTime     string  `json:"register_time"`
	StatusFormat     string  `json:"status_format"`
	AgentName        string  `json:"agent_name"`
}

// CustomerListResponse — response trả cho client.
type CustomerListResponse struct {
	Data  []UpstreamUser `json:"data"`
	Total int            `json:"total"`
	Page  int            `json:"page"`
	Limit int            `json:"limit"`
}
