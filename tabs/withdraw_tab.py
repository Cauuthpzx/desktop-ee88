"""
tabs/withdraw_tab.py — Tab Rút tiền (upstream: /agent/withdrawalsRecord.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


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

    def _fetch_upstream(self, agent_id, page, limit, search):
        return upstream.fetch_withdrawals(
            agent_id=agent_id, page=page, limit=limit, username=search,
        )

    def _formatters(self):
        return {
            "amount": lambda v: currency(float(v)) if v else "0",
            "user_fee": lambda v: currency(float(v)) if v else "0",
            "true_amount": lambda v: currency(float(v)) if v else "0",
        }
