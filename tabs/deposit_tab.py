"""
tabs/deposit_tab.py — Tab Nạp tiền (upstream: /agent/depositAndWithdrawal.html)
"""
from tabs._upstream_tab import UpstreamTab, _fmt_currency
from utils.upstream import upstream
from core.i18n import t
from core import theme
from widgets.stat_card import StatCard


class DepositTab(UpstreamTab):
    _title_key = "deposit.title"
    _data_type = "deposits"
    _columns_keys = [
        ("deposit.col_agent",   "_agentName"),
        ("deposit.col_account", "username"),
        ("deposit.col_parent",  "user_parent_format"),
        ("deposit.col_amount",  "amount"),
        ("deposit.col_type",    "type"),
        ("deposit.col_status",  "status"),
        ("deposit.col_time",    "create_time"),
    ]
    _summary_keys = [
        ("deposit.col_amount", "amount"),
    ]
    _search_fields = [
        {"key": "create_time", "type": "date_range",
         "label": "search.create_time", "default": "today"},
        {"key": "username", "type": "text",
         "label": "search.username", "placeholder": "search.username_ph",
         "width": 200},
        {"key": "type", "type": "select", "label": "search.transaction_type",
         "options": [
             ("search.all", ""),
             ("search.type_deposit", "1"),
             ("search.type_withdraw", "2"),
         ], "width": 180},
        {"key": "status", "type": "select", "label": "search.transaction_status",
         "options": [
             ("search.all", ""),
             ("search.txn_pending", "0"),
             ("search.txn_complete", "1"),
             ("search.txn_processing", "2"),
             ("search.txn_failed", "3"),
         ], "width": 180},
    ]

    def _fetch_upstream(self, agent_id, page, limit, **params):
        return upstream.fetch_deposits(
            agent_id=agent_id, page=page, limit=limit, **params,
        )

    def _formatters(self):
        return {"amount": _fmt_currency}

    def _build_extra_cards(self, title_row) -> None:
        self._card_status = StatCard(
            t("deposit.card_status"), "0 / 0",
            min_width=80, value_size=theme.FONT_SIZE_LG)
        self._card_orders = StatCard(
            t("deposit.card_orders"), "0",
            min_width=80, value_size=theme.FONT_SIZE_LG)
        title_row.addWidget(self._card_status, 1)
        title_row.addWidget(self._card_orders, 1)

    def _update_extra_cards(self) -> None:
        if self._group_mode:
            # Group mode: all data loaded — count locally
            self._count_from_rows()
        else:
            # Single agent: fetch counts from upstream API
            self._fetch_status_counts()

    def _count_from_rows(self) -> None:
        complete = sum(1 for r in self._all_rows if str(r.get("status", "")) == "1")
        failed = sum(1 for r in self._all_rows if str(r.get("status", "")) == "3")
        processing = sum(1 for r in self._all_rows if str(r.get("status", "")) == "2")
        self._card_status.update_value(f"{complete} / {failed}")
        self._card_orders.update_value(str(complete + processing + failed))

    def _fetch_status_counts(self) -> None:
        """Fetch counts per status from upstream (limit=1, chỉ lấy count)."""
        if not self._current_agent_id:
            return
        aid = self._current_agent_id
        params = self._get_search_params()
        params.pop("status", None)

        from utils.thread_worker import run_in_thread

        def _fetch_counts():
            results = {}
            for status_code in ("1", "2", "3"):
                p = {**params, "status": status_code}
                data = self._fetch_upstream(aid, 1, 1, **p)
                results[status_code] = data.get("count", 0)
            return results

        run_in_thread(
            _fetch_counts,
            on_result=self._on_status_counts,
        )

    def _on_status_counts(self, counts: dict) -> None:
        complete = counts.get("1", 0)
        failed = counts.get("3", 0)
        processing = counts.get("2", 0)
        self._card_status.update_value(f"{complete} / {failed}")
        self._card_orders.update_value(str(complete + processing + failed))

    def retranslate(self) -> None:
        super().retranslate()
        self._card_status.set_title(t("deposit.card_status"))
        self._card_orders.set_title(t("deposit.card_orders"))
