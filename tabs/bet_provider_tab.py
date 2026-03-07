"""
tabs/bet_provider_tab.py — Tab Đơn cược nhà cung cấp (upstream: /agent/betOrder.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


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
    _search_fields = [
        {"key": "bet_time", "type": "date_range",
         "label": "search.bet_time", "default": "today"},
        {"key": "serial_no", "type": "text",
         "label": "search.serial_no", "placeholder": "search.serial_no_ph",
         "width": 200},
        {"key": "platform_username", "type": "text",
         "label": "search.platform_account",
         "placeholder": "search.platform_account_ph",
         "width": 180},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_bet_provider(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "bet_amount": _fmt_currency,
            "turnover": _fmt_currency,
            "prize": _fmt_currency,
            "win_lose": _fmt_currency,
        }
