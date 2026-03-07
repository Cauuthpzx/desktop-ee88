"""
tabs/deposit_tab.py — Tab Nạp tiền (upstream: /agent/depositAndWithdrawal.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


class DepositTab(UpstreamTab):
    _title_key = "deposit.title"
    _data_type = "deposits"
    _columns_keys = [
        ("deposit.col_agent",   "_agentName"),
        ("deposit.col_account", "username"),
        ("deposit.col_parent",  "user_parent_format"),
        ("deposit.col_amount",  "amount"),
        ("deposit.col_type",    "type"),
        ("deposit.col_status",  "status"),
        ("deposit.col_time",    "create_time"),
    ]
    _summary_keys = [
        ("deposit.col_amount", "amount"),
    ]
    _search_fields = [
        {"key": "create_time", "type": "date_range",
         "label": "search.create_time", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 200},
        {"key": "type", "type": "select", "label": "search.transaction_type",
         "options": [
             ("search.all", ""),
             ("search.type_deposit", "1"),
             ("search.type_withdraw", "2"),
         ], "width": 180},
        {"key": "status", "type": "select", "label": "search.transaction_status",
         "options": [
             ("search.all", ""),
             ("search.txn_pending", "0"),
             ("search.txn_complete", "1"),
             ("search.txn_processing", "2"),
             ("search.txn_failed", "3"),
         ], "width": 180},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_deposits(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {"amount": _fmt_currency}
