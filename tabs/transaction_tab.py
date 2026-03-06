"""
tabs/transaction_tab.py — Tab Giao dịch / Sao kê (upstream: /agent/reportFunds.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


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

    def _fetch_upstream(self, agent_id, page, limit, search):
        return upstream.fetch_transactions(
            agent_id=agent_id, page=page, limit=limit, username=search,
        )

    def _formatters(self):
        fmt = lambda v: currency(float(v)) if v else "0"
        return {
            "deposit_amount": fmt,
            "withdrawal_amount": fmt,
            "charge_fee": fmt,
            "agent_commission": fmt,
            "promotion": fmt,
            "third_rebate": fmt,
            "third_activity_amount": fmt,
        }
