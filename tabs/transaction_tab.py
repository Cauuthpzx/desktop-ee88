"""
tabs/transaction_tab.py — Tab Giao dịch / Sao kê (upstream: /agent/reportFunds.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


class TransactionTab(UpstreamTab):
    _title_key = "transaction.title"
    _columns_keys = [
        ("transaction.col_agent",       "_agentName"),
        ("transaction.col_account",     "username"),
        ("transaction.col_parent",      "user_parent_format"),
        ("transaction.col_deposit_n",   "deposit_count"),
        ("transaction.col_deposit_amt", "deposit_amount"),
        ("transaction.col_withdraw_n",  "withdrawal_count"),
        ("transaction.col_withdraw_amt","withdrawal_amount"),
        ("transaction.col_fee",         "charge_fee"),
        ("transaction.col_commission",  "agent_commission"),
        ("transaction.col_promo",       "promotion"),
        ("transaction.col_3rd_rebate",  "third_rebate"),
        ("transaction.col_3rd_bonus",   "third_activity_amount"),
        ("transaction.col_date",        "date"),
    ]
    _search_fields = [
        {"key": "date", "type": "date_range",
         "label": "search.date", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 200},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_transactions(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "deposit_amount": _fmt_currency,
            "withdrawal_amount": _fmt_currency,
            "charge_fee": _fmt_currency,
            "agent_commission": _fmt_currency,
            "promotion": _fmt_currency,
            "third_rebate": _fmt_currency,
            "third_activity_amount": _fmt_currency,
        }
