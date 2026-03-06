"""
tabs/deposit_tab.py — Tab Nạp tiền (upstream: /agent/depositAndWithdrawal.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


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

    def _fetch_upstream(self, agent_id, page, limit, search):
        return upstream.fetch_deposits(
            agent_id=agent_id, page=page, limit=limit, username=search,
        )

    def _formatters(self):
        return {
            "amount": lambda v: currency(float(v)) if v else "0",
        }
