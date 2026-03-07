"""
tabs/customer_tab.py — Tab Khách hàng (upstream: /agent/user.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


class CustomerTab(UpstreamTab):
    _title_key = "customer.title"
    _data_type = "customers"
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
         "label": "search.first_deposit_time", "optional": True},
        {"key": "status", "type": "select", "label": "search.status",
         "options": [
             ("search.all", ""),
             ("search.status_unrated", "0"),
             ("search.status_normal", "1"),
             ("search.status_frozen", "2"),
             ("search.status_locked", "3"),
         ]},
        {"key": "sort_field", "type": "select", "label": "search.sort_field",
         "options": [
             ("search.sort_select", ""),
             ("search.sort_balance", "money"),
             ("search.sort_last_login", "login_time"),
             ("search.sort_register", "register_time"),
             ("search.sort_deposit", "deposit_money"),
             ("search.sort_withdraw", "withdrawal_money"),
         ], "width": 150},
        {"key": "sort_direction", "type": "select", "label": "search.sort_direction",
         "options": [
             ("search.sort_desc", "desc"),
             ("search.sort_asc", "asc"),
         ], "width": 150},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_customers(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "money": _fmt_currency,
            "deposit_amount": _fmt_currency,
            "withdrawal_amount": _fmt_currency,
        }
