"""
tabs/provider_tab.py — Tab Nhà cung cấp (upstream: /agent/reportThirdGame.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


class ProviderTab(UpstreamTab):
    _title_key = "provider.title"
    _columns_keys = [
        ("provider.col_agent",    "_agentName"),
        ("provider.col_account",  "username"),
        ("provider.col_provider", "platform_id_name"),
        ("provider.col_bet_n",    "t_bet_times"),
        ("provider.col_bet_amt",  "t_bet_amount"),
        ("provider.col_valid",    "t_turnover"),
        ("provider.col_prize",    "t_prize"),
        ("provider.col_result",   "t_win_lose"),
    ]

    def _fetch_upstream(self, agent_id, page, limit, search):
        return upstream.fetch_provider(
            agent_id=agent_id, page=page, limit=limit, username=search,
        )

    def _formatters(self):
        fmt = lambda v: currency(float(v)) if v else "0"
        return {
            "t_bet_amount": fmt,
            "t_turnover": fmt,
            "t_prize": fmt,
            "t_win_lose": fmt,
        }
