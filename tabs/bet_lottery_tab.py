"""
tabs/bet_lottery_tab.py — Tab Đơn cược xổ số (upstream: /agent/bet.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream
from utils.formatters import currency


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

    def _fetch_upstream(self, agent_id, page, limit, search):
        return upstream.fetch_bet_lottery(
            agent_id=agent_id, page=page, limit=limit, username=search,
        )

    def _formatters(self):
        fmt = lambda v: currency(float(v)) if v else "0"
        return {
            "money": fmt,
            "rebate_amount": fmt,
            "result": fmt,
        }
