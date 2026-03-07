"""
tabs/bet_lottery_tab.py — Tab Đơn cược xổ số (upstream: /agent/bet.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream


class BetLotteryTab(UpstreamTab):
    _title_key = "bet_lottery.title"
    _columns_keys = [
        ("bet_lottery.col_agent",    "_agentName"),
        ("bet_lottery.col_serial",   "serial_no"),
        ("bet_lottery.col_user",     "username"),
        ("bet_lottery.col_time",     "create_time"),
        ("bet_lottery.col_game",     "lottery_name"),
        ("bet_lottery.col_type",     "play_type_name"),
        ("bet_lottery.col_method",   "play_name"),
        ("bet_lottery.col_period",   "issue"),
        ("bet_lottery.col_info",     "content"),
        ("bet_lottery.col_amount",   "money"),
        ("bet_lottery.col_rebate",   "rebate_amount"),
        ("bet_lottery.col_result",   "result"),
        ("bet_lottery.col_status",   "status_text"),
    ]
    _search_fields = [
        {"key": "create_time", "type": "date_range",
         "label": "search.bet_time", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 150},
        {"key": "serial_no", "type": "text",
         "label": "search.serial_no", "placeholder": "search.serial_no_ph",
         "width": 180},
        {"key": "status", "type": "select", "label": "search.status",
         "options": [
             ("search.all", ""),
             ("search.bet_pending", "0"),
             ("search.bet_won", "1"),
             ("search.bet_lost", "2"),
             ("search.bet_tie", "3"),
             ("search.bet_cancelled", "4"),
         ], "width": 120},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_bet_lottery(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "money": _fmt_currency,
            "rebate_amount": _fmt_currency,
            "result": _fmt_currency,
        }
