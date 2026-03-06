"""
tabs/referral_tab.py — Tab Mã giới thiệu (upstream: /agent/inviteList.html)
"""
from tabs._upstream_tab import UpstreamTab
from utils.upstream import upstream


class ReferralTab(UpstreamTab):
    _title_key = "referral.title"
    _columns_keys = [
        ("referral.col_agent",          "_agentName"),
        ("referral.col_code",           "invite_code"),
        ("referral.col_type",           "user_type"),
        ("referral.col_total_reg",      "reg_count"),
        ("referral.col_user_reg",       "scope_reg_count"),
        ("referral.col_depositors",     "recharge_count"),
        ("referral.col_first_deposit",  "first_recharge_count"),
        ("referral.col_first_amount",   "register_recharge_count"),
        ("referral.col_remark",         "remark"),
        ("referral.col_time",           "create_time"),
    ]
    _search_fields = [
        {"key": "create_time", "type": "date_range",
         "label": "search.create_time"},
        {"key": "invite_code", "type": "text",
         "label": "search.invite_code", "placeholder": "search.invite_code_ph",
         "width": 200},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_referrals(
            agent_id=agent_id, page=page, limit=limit, **params,
        )
