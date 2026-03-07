"""
tabs/lottery_tab.py — Tab Xổ số (upstream: /agent/reportLottery.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from tabs.bet_lottery_tab import _LOTTERY_OPTIONS
from utils.upstream import upstream


class LotteryTab(UpstreamTab):
    _title_key = "lottery.title"
    _columns_keys = [
        ("lottery.col_agent",    "_agentName"),
        ("lottery.col_account",  "username"),
        ("lottery.col_parent",   "user_parent_format"),
        ("lottery.col_bet_n",    "bet_count"),
        ("lottery.col_bet_amt",  "bet_amount"),
        ("lottery.col_valid",    "valid_amount"),
        ("lottery.col_rebate",   "rebate_amount"),
        ("lottery.col_result",   "result"),
        ("lottery.col_winlose",  "win_lose"),
        ("lottery.col_prize",    "prize"),
        ("lottery.col_name",     "lottery_name"),
    ]
    _summary_keys = [
        ("lottery.col_bet_amt",  "bet_amount"),
        ("lottery.col_valid",    "valid_amount"),
        ("lottery.col_rebate",   "rebate_amount"),
        ("lottery.col_result",   "result"),
        ("lottery.col_winlose",  "win_lose"),
        ("lottery.col_prize",    "prize"),
    ]
    _search_fields = [
        {"key": "date", "type": "date_range",
         "label": "search.date", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 200},
        {"key": "lottery_id", "type": "select", "label": "search.lottery_name",
         "options": _LOTTERY_OPTIONS, "width": 200},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_lottery(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {
            "bet_amount": _fmt_currency,
            "valid_amount": _fmt_currency,
            "rebate_amount": _fmt_currency,
            "result": _fmt_currency,
            "win_lose": _fmt_currency,
            "prize": _fmt_currency,
        }
