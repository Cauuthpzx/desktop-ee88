"""
tabs/customer_tab.py — Tab Khach hang (local-first, infinite scroll).

Flow:
- showEvent → doc agents tu QSettings (0ms) → hien combo ngay
- Neu co agent active + cookie → fetch upstream truc tiep (skip DB)
- Scroll toi cuoi → tu dong load trang tiep theo (infinite scroll)
"""
from PyQt6.QtWidgets import QComboBox, QTableWidgetItem
from PyQt6.QtCore import Qt

from core.base_widgets import BaseTab, label, divider, hbox
from core import theme
from core.i18n import t
from utils.upstream import upstream
from utils.formatters import currency
from utils.thread_worker import run_in_thread
from widgets.table_crud import TableCrud
from widgets.loading import LoadingOverlay
from dialogs.confirm_dialog import error

COLUMNS_KEYS = [
    ("customer.col_username",    "username"),
    ("customer.col_type",        "type_format"),
    ("customer.col_agent",       "parent_user"),
    ("customer.col_balance",     "money"),
    ("customer.col_deposit_n",   "deposit_count"),
    ("customer.col_withdraw_n",  "withdrawal_count"),
    ("customer.col_deposit_amt", "deposit_amount"),
    ("customer.col_withdraw_amt", "withdrawal_amount"),
    ("customer.col_last_login",  "login_time"),
    ("customer.col_register",    "register_time"),
    ("customer.col_status",      "status_format"),
]

PAGE_SIZE = 100


class CustomerTab(BaseTab):
    def _build(self, layout) -> None:
        self._title_lbl = label(t("customer.title"), bold=True, size=theme.FONT_SIZE_LG)
        layout.addWidget(self._title_lbl)
        layout.addWidget(divider())

        # Agent selector
        agent_row = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        self._agent_label = label(t("customer.agent_select"))
        agent_row.addWidget(self._agent_label)
        self._agent_combo = QComboBox()
        self._agent_combo.setMinimumWidth(200)
        self._agent_combo.currentIndexChanged.connect(self._on_agent_changed)
        agent_row.addWidget(self._agent_combo)
        agent_row.addStretch()
        layout.addLayout(agent_row)

        # Table + pagination + infinite scroll
        columns = [t(ck[0]) for ck in COLUMNS_KEYS]
        self.crud = TableCrud(
            columns=columns,
            on_add=None, on_edit=None, on_delete=None,
            on_search=self._on_search,
            on_page_change=self._on_page,
            page_size=PAGE_SIZE,
        )
        for btn in self.crud._toolbar._buttons.values():
            btn.hide()
        layout.addWidget(self.crud)

        # Infinite scroll: detect scroll to bottom
        self._scrollbar = self.crud.table.verticalScrollBar()
        self._scrollbar.valueChanged.connect(self._on_scroll)

        self._loading = LoadingOverlay(self)
        self._agents: list[dict] = []
        self._current_agent_id: int | None = None
        self._search_text = ""
        self._first_show = True

        # Infinite scroll state
        self._current_page = 0
        self._total_count = 0
        self._is_loading = False
        self._all_rows: list[dict] = []

    # ── Show — instant from local cache ──────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            self._load_from_cache()

    def _load_from_cache(self) -> None:
        """Doc agents tu QSettings (0ms) → populate combo → fetch data."""
        agents = upstream.get_agents_local()
        if agents:
            self._apply_agents(agents)
        else:
            self._agent_combo.addItem(t("customer.no_active_agent"))

    # ── Agent combo ──────────────────────────────────────────

    def _apply_agents(self, agents: list[dict]) -> None:
        self._agents = [a for a in agents if a.get("status") == "active"]

        self._agent_combo.blockSignals(True)
        self._agent_combo.clear()
        if not self._agents:
            self._agent_combo.addItem(t("customer.no_active_agent"))
            self._current_agent_id = None
        else:
            for ag in self._agents:
                self._agent_combo.addItem(
                    f"{ag['name']} ({ag['ext_username']})", ag["id"],
                )
            self._current_agent_id = self._agents[0]["id"]
        self._agent_combo.blockSignals(False)

        if self._current_agent_id:
            self._reload_fresh()

    def _on_agent_changed(self, index: int) -> None:
        if index < 0 or not self._agents:
            return
        self._current_agent_id = self._agent_combo.currentData()
        if self._current_agent_id:
            self._reload_fresh()

    # ── Data loading (infinite scroll) ───────────────────────

    def _reload_fresh(self) -> None:
        """Reset va load trang 1."""
        self._current_page = 0
        self._total_count = 0
        self._all_rows = []
        self._load_next_page()

    def _load_next_page(self) -> None:
        """Fetch trang tiep theo tu upstream."""
        if not self._current_agent_id or self._is_loading:
            return
        # Da load het?
        if self._current_page > 0 and len(self._all_rows) >= self._total_count:
            return

        self._is_loading = True
        aid = self._current_agent_id
        search = self._search_text
        page = self._current_page + 1

        run_in_thread(
            lambda: upstream.fetch_customers(
                agent_id=aid, page=page, limit=PAGE_SIZE, username=search,
            ),
            on_result=lambda data: self._on_page_data(data, page),
            on_error=self._on_error,
            on_finished=self._on_load_finished,
        )
        if self._current_page == 0:
            self._loading.start(t("loading.loading_data"))

    def _on_page_data(self, data: dict, page: int) -> None:
        rows = data.get("data", [])
        self._total_count = data.get("count", 0)
        self._current_page = page

        if page == 1:
            # Trang dau: replace table
            self._all_rows = rows
            self._render_table(self._all_rows)
        else:
            # Trang tiep: append rows
            self._all_rows.extend(rows)
            self._append_rows(rows)

        # Update pagination widget
        self.crud.set_total(self._total_count, reset_page=False)
        if self.crud._pager:
            self.crud._pager._current = page
            self.crud._pager._refresh()

    def _render_table(self, rows: list[dict]) -> None:
        """Render toan bo table (dung cho trang 1)."""
        keys = [ck[1] for ck in COLUMNS_KEYS]
        formatters = {
            "money": lambda v: currency(float(v)) if v else "0",
            "deposit_amount": lambda v: currency(float(v)) if v else "0",
            "withdrawal_amount": lambda v: currency(float(v)) if v else "0",
        }
        self.crud.load(rows, keys=keys, id_key="id", formatters=formatters)

    def _append_rows(self, rows: list[dict]) -> None:
        """Append them rows vao cuoi table (khong xoa rows cu)."""
        keys = [ck[1] for ck in COLUMNS_KEYS]
        formatters = {
            "money": lambda v: currency(float(v)) if v else "0",
            "deposit_amount": lambda v: currency(float(v)) if v else "0",
            "withdrawal_amount": lambda v: currency(float(v)) if v else "0",
        }
        table = self.crud.table
        center = Qt.AlignmentFlag.AlignCenter
        start_row = table.rowCount()

        table.setUpdatesEnabled(False)
        table.setRowCount(start_row + len(rows))

        for i, rec in enumerate(rows):
            row = start_row + i
            for col, key in enumerate(keys):
                val = rec.get(key, "")
                if key in formatters:
                    display = formatters[key](val)
                else:
                    display = str(val) if val is not None else ""
                item = QTableWidgetItem(display)
                item.setTextAlignment(center)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, rec.get("id"))
                table.setItem(row, col, item)

        table.setUpdatesEnabled(True)

    def _on_jump_data(self, data: dict, page: int) -> None:
        """Khi user click pagination nhay trang."""
        rows = data.get("data", [])
        self._total_count = data.get("count", 0)
        self._current_page = page
        self._all_rows = rows
        self._render_table(rows)
        self.crud.set_total(self._total_count, reset_page=False)
        if self.crud._pager:
            self.crud._pager._current = page
            self.crud._pager._refresh()

    def _on_load_finished(self) -> None:
        self._is_loading = False
        self._loading.stop()

    def _on_error(self, exc: Exception) -> None:
        if isinstance(exc, (PermissionError, ValueError)):
            error(self.window(), t("customer.session_expired"))
        else:
            error(self.window(), t("customer.error_load"))

    # ── Infinite scroll detection ────────────────────────────

    def _on_scroll(self, value: int) -> None:
        sb = self._scrollbar
        # Khi scroll gan cuoi (con 20% viewport height)
        if sb.maximum() == 0:
            return
        remaining = sb.maximum() - value
        threshold = max(50, self.crud.table.viewport().height() // 5)
        if remaining <= threshold:
            self._load_next_page()

    # ── Search & Pagination click ────────────────────────────

    def _on_search(self, text: str) -> None:
        self._search_text = text.strip()
        self._reload_fresh()

    def _on_page(self, page: int) -> None:
        """User click pagination → load trang do, reset table."""
        if self._is_loading:
            return
        self._current_page = page - 1  # _load_next_page se +1
        self._all_rows = []
        self._is_loading = False

        # Load trang duoc chon, replace table
        self._is_loading = True
        aid = self._current_agent_id
        search = self._search_text

        run_in_thread(
            lambda: upstream.fetch_customers(
                agent_id=aid, page=page, limit=PAGE_SIZE, username=search,
            ),
            on_result=lambda data: self._on_jump_data(data, page),
            on_error=self._on_error,
            on_finished=self._on_load_finished,
        )
        self._loading.start(t("loading.loading_data"))

    # ── Public: reload from outside (e.g. after agent login) ─

    def refresh_agents(self) -> None:
        """Goi khi agents thay doi (login/logout agent)."""
        agents = upstream.get_agents_local()
        if agents:
            self._apply_agents(agents)

    # ── Retranslate ──────────────────────────────────────────

    def retranslate(self) -> None:
        self._title_lbl.setText(t("customer.title"))
        self._agent_label.setText(t("customer.agent_select"))
        columns = [t(ck[0]) for ck in COLUMNS_KEYS]
        self.crud.table.setHorizontalHeaderLabels(columns)
