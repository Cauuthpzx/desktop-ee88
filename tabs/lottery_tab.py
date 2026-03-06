"""
tabs/lottery_tab.py — Tab Xổ số (upstream: /agent/reportLottery.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


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

    def _fetch_upstream(self, agent_id, page, limit, search):
        return upstream.fetch_lottery(
            agent_id=agent_id, page=page, limit=limit, username=search,
        )

    def _formatters(self):
        fmt = lambda v: currency(float(v)) if v else "0"
        return {
            "bet_amount": fmt,
            "valid_amount": fmt,
            "rebate_amount": fmt,
            "result": fmt,
            "win_lose": fmt,
            "prize": fmt,
        }
