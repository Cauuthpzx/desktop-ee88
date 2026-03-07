"""
tabs/deposit_tab.py — Tab Nạp tiền (upstream: /agent/depositAndWithdrawal.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


class DepositTab(UpstreamTab):
    _title_key = "deposit.title"
    _columns_keys = [
        ("deposit.col_agent",   "_agentName"),
        ("deposit.col_account", "username"),
        ("deposit.col_parent",  "user_parent_format"),
        ("deposit.col_amount",  "amount"),
        ("deposit.col_type",    "type"),
        ("deposit.col_status",  "status"),
        ("deposit.col_time",    "create_time"),
    ]
    _search_fields = [
        {"key": "create_time", "type": "date_range",
         "label": "search.create_time", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 160},
        {"key": "type", "type": "select", "label": "search.transaction_type",
         "options": [
             ("search.all", ""),
             ("search.deposit_online", "1"),
             ("search.deposit_manual", "2"),
             ("search.deposit_activity", "3"),
         ], "width": 140},
        {"key": "status", "type": "select", "label": "search.status",
         "options": [
             ("search.all", ""),
             ("search.status_pending", "0"),
             ("search.status_success", "1"),
             ("search.status_rejected", "2"),
         ], "width": 130},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_deposits(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {"amount": _fmt_currency}
