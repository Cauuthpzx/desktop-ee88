"""
tabs/provider_tab.py — Tab Nhà cung cấp (upstream: /agent/reportThirdGame.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


# Danh sách nhà cung cấp game bên thứ 3 — từ upstream
_PROVIDER_OPTIONS = [
    ("search.all", ""),
    ("PA", "8"),
    ("BBIN", "9"),
    ("WM", "10"),
    ("MINI", "14"),
    ("KY", "20"),
    ("PGSOFT", "28"),
    ("LUCKYWIN", "29"),
    ("SABA", "30"),
    ("PT", "31"),
    ("RICH88", "38"),
    ("ASTAR", "43"),
    ("FB", "45"),
    ("JILI", "46"),
    ("KA", "47"),
    ("MW", "48"),
    ("SBO", "50"),
    ("NEXTSPIN", "51"),
    ("AMB", "52"),
    ("FunTa", "53"),
    ("MG", "62"),
    ("WS168", "63"),
    ("DG CASINO", "69"),
    ("V8", "70"),
    ("AE", "71"),
    ("TP", "72"),
    ("FC", "73"),
    ("JDB", "74"),
    ("CQ9", "75"),
    ("PP", "76"),
    ("VA", "77"),
    ("BNG", "78"),
    ("DB CASINO", "84"),
    ("EVO CASINO", "85"),
    ("CMD SPORTS", "90"),
    ("PG NEW", "91"),
    ("FBLIVE", "92"),
    ("ON CASINO", "93"),
    ("MT", "94"),
    ("fC NEW", "102"),
]


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
    _search_fields = [
        {"key": "date", "type": "date_range",
         "label": "search.date", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 200},
        {"key": "platform_id", "type": "select", "label": "search.game_provider",
         "options": _PROVIDER_OPTIONS, "width": 200},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_provider(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "t_bet_amount": _fmt_currency,
            "t_turnover": _fmt_currency,
            "t_prize": _fmt_currency,
            "t_win_lose": _fmt_currency,
        }
