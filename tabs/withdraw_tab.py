"""
tabs/withdraw_tab.py — Tab Rút tiền (upstream: /agent/withdrawalsRecord.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


class WithdrawTab(UpstreamTab):
    _title_key = "withdraw.title"
    _columns_keys = [
        ("withdraw.col_agent",      "_agentName"),
        ("withdraw.col_serial",     "serial_no"),
        ("withdraw.col_time",       "create_time"),
        ("withdraw.col_account",    "username"),
        ("withdraw.col_parent",     "user_parent_format"),
        ("withdraw.col_amount",     "amount"),
        ("withdraw.col_fee",        "user_fee"),
        ("withdraw.col_actual",     "true_amount"),
        ("withdraw.col_status",     "status_format"),
        ("withdraw.col_action",     "operation"),
    ]
    _summary_keys = [
        ("withdraw.col_amount",  "amount"),
        ("withdraw.col_fee",     "user_fee"),
        ("withdraw.col_actual",  "true_amount"),
    ]
    _search_fields = [
        {"key": "create_time", "type": "date_range",
         "label": "search.create_time", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 150},
        {"key": "serial_no", "type": "text",
         "label": "search.serial_no", "placeholder": "search.serial_no_ph",
         "width": 300},
        {"key": "status", "type": "select", "label": "search.transaction_status",
         "options": [
             ("search.all", ""),
             ("search.txn_pending", "0"),
             ("search.txn_complete", "1"),
             ("search.txn_processing", "2"),
             ("search.txn_failed", "3"),
         ], "width": 200},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_withdrawals(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "amount": _fmt_currency,
            "user_fee": _fmt_currency,
            "true_amount": _fmt_currency,
        }
