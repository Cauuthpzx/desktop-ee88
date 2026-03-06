"""
tabs/customer_tab.py — Tab Khách hàng (upstream: /agent/user.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


class CustomerTab(UpstreamTab):
    _title_key = "customer.title"
    _columns_keys = [
        ("customer.col_username",    "username"),
        ("customer.col_type",        "type_format"),
        ("customer.col_agent",       "parent_user"),
        ("customer.col_balance",     "money"),
        ("customer.col_deposit_n",   "deposit_count"),
        ("customer.col_withdraw_n",  "withdrawal_count"),
        ("customer.col_deposit_amt", "deposit_amount"),
        ("customer.col_withdraw_amt", "withdrawal_amount"),
        ("customer.col_last_login",  "login_time"),
        ("customer.col_register",    "register_time"),
        ("customer.col_status",      "status_format"),
    ]
    _search_fields = [
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 160},
        {"key": "first_deposit_time", "type": "date_range",
         "label": "search.first_deposit_time"},
        {"key": "status", "type": "select", "label": "search.status",
         "options": [
             ("search.all", ""),
             ("search.status_normal", "0"),
             ("search.status_frozen", "1"),
         ]},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_customers(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        fmt = lambda v: currency(float(v)) if v else "0"
        return {
            "money": fmt,
            "deposit_amount": fmt,
            "withdrawal_amount": fmt,
        }
