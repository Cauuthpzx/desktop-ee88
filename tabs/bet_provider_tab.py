"""
tabs/bet_provider_tab.py — Tab Đơn cược nhà cung cấp (upstream: /agent/betOrder.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


class BetProviderTab(UpstreamTab):
    _title_key = "bet_provider.title"
    _columns_keys = [
        ("bet_provider.col_agent",      "_agentName"),
        ("bet_provider.col_serial",     "serial_no"),
        ("bet_provider.col_provider",   "platform_id_name"),
        ("bet_provider.col_platform",   "platform_username"),
        ("bet_provider.col_game_type",  "c_name"),
        ("bet_provider.col_game_name",  "game_name"),
        ("bet_provider.col_bet",        "bet_amount"),
        ("bet_provider.col_valid",      "turnover"),
        ("bet_provider.col_prize",      "prize"),
        ("bet_provider.col_result",     "win_lose"),
        ("bet_provider.col_time",       "bet_time"),
    ]

    def _fetch_upstream(self, agent_id, page, limit, search):
        return upstream.fetch_bet_provider(
            agent_id=agent_id, page=page, limit=limit, username=search,
        )

    def _formatters(self):
        fmt = lambda v: currency(float(v)) if v else "0"
        return {
            "bet_amount": fmt,
            "turnover": fmt,
            "prize": fmt,
            "win_lose": fmt,
        }
