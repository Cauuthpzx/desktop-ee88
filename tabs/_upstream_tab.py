"""
tabs/_upstream_tab.py — Base class cho cac tab fetch data tu upstream.

Pattern chung:
- Agent selector combo
- Search filter row (text, date range, select)
- TableCrud + pagination + infinite scroll
- Fetch upstream truc tiep bang cookies local
- Cac tab con chi can khai bao: _columns_keys, _title_key, _search_fields,
  _fetch_upstream(), _formatters()
"""
from PyQt6.QtWidgets import (
    QComboBox, QTableWidgetItem, QLineEdit, QDateEdit,
    QHBoxLayout, QPushButton, QLabel, QWidget,
)
from PyQt6.QtCore import Qt, QDate

from core.base_widgets import BaseTab, label, divider, hbox
from core import theme
from core.i18n import t
from utils.upstream import upstream
from utils.formatters import currency
from utils.thread_worker import run_in_thread
from widgets.table_crud import TableCrud
from widgets.loading import LoadingOverlay
from dialogs.confirm_dialog import error

PAGE_SIZE = 100


class UpstreamTab(BaseTab):
    """Base tab cho cac tab fetch data tu upstream EE88.

    Subclass PHAI override:
        _title_key: str           — i18n key cho title (e.g. "deposit.title")
        _columns_keys: list       — [(i18n_key, data_key), ...]
        _fetch_upstream(aid, page, limit, **params) → dict

    Optional override:
        _search_fields: list      — field definitions for search row
        _formatters() → dict      — column formatters
    """
    _title_key: str = ""
    _columns_keys: list[tuple[str, str]] = []
    _search_fields: list[dict] = []

    def _build(self, layout) -> None:
        self._title_lbl = label(t(self._title_key), bold=True, size=theme.FONT_SIZE_LG)
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

        # Search filter row
        self._filter_widgets: dict[str, QWidget] = {}
        self._filter_labels: dict[str, QLabel] = {}
        if self._search_fields:
            self._build_filters(layout)

        # Table + pagination + infinite scroll
        columns = [t(ck[0]) for ck in self._columns_keys]
        self.crud = TableCrud(
            columns=columns,
            on_add=None, on_edit=None, on_delete=None,
            on_search=None,
            on_page_change=self._on_page,
            page_size=PAGE_SIZE,
        )
        for btn in self.crud._toolbar._buttons.values():
            btn.hide()
        # Hide toolbar completely since we have our own filter row
        self.crud._toolbar.hide()
        layout.addWidget(self.crud)

        # Infinite scroll
        self._scrollbar = self.crud.table.verticalScrollBar()
        self._scrollbar.valueChanged.connect(self._on_scroll)

        self._loading = LoadingOverlay(self)
        self._agents: list[dict] = []
        self._current_agent_id: int | None = None
        self._first_show = True

        # Infinite scroll state
        self._current_page = 0
        self._total_count = 0
        self._is_loading = False
        self._all_rows: list[dict] = []

    # ── Search filter row ──────────────────────────────────

    def _build_filters(self, layout) -> None:
        """Build search filter widgets from _search_fields.

        Each field dict:
            {"key": "username", "type": "text", "label": "search.username",
             "placeholder": "search.username_ph", "width": 160}
            {"key": "date", "type": "date_range", "label": "search.date"}
            {"key": "status", "type": "select", "label": "search.status",
             "options": [("search.all", ""), ("search.active", "1"), ...]}
        """
        row = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)

        for field in self._search_fields:
            ftype = field.get("type", "text")
            key = field["key"]

            # Label
            lbl = QLabel(t(field["label"]))
            row.addWidget(lbl)
            self._filter_labels[key] = lbl

            if ftype == "text":
                w = QLineEdit()
                w.setPlaceholderText(t(field.get("placeholder", "crud.search")))
                w.setMinimumWidth(field.get("width", 150))
                w.returnPressed.connect(self._on_filter_search)
                row.addWidget(w)

            elif ftype == "date_range":
                w = QWidget()
                dl = QHBoxLayout(w)
                dl.setContentsMargins(0, 0, 0, 0)
                dl.setSpacing(theme.SPACING_XS)

                d_from = QDateEdit()
                d_from.setCalendarPopup(True)
                d_from.setDate(QDate.currentDate().addDays(-7))
                d_from.setDisplayFormat("yyyy-MM-dd")
                dl.addWidget(d_from)

                dl.addWidget(QLabel("~"))

                d_to = QDateEdit()
                d_to.setCalendarPopup(True)
                d_to.setDate(QDate.currentDate())
                d_to.setDisplayFormat("yyyy-MM-dd")
                dl.addWidget(d_to)

                w._d_from = d_from
                w._d_to = d_to
                row.addWidget(w)

            elif ftype == "select":
                w = QComboBox()
                for opt_label, opt_val in field.get("options", []):
                    w.addItem(t(opt_label), opt_val)
                w.setMinimumWidth(field.get("width", 120))
                row.addWidget(w)

            self._filter_widgets[key] = w

        # Search button
        self._btn_search = QPushButton(t("crud.search"))
        self._btn_search.clicked.connect(self._on_filter_search)
        row.addWidget(self._btn_search)

        row.addStretch()
        layout.addLayout(row)

    def _get_search_params(self) -> dict[str, str]:
        """Collect search params from filter widgets."""
        params: dict[str, str] = {}
        for field in self._search_fields:
            key = field["key"]
            w = self._filter_widgets.get(key)
            if not w:
                continue

            ftype = field.get("type", "text")
            param_key = field.get("param", key)

            if ftype == "text":
                val = w.text().strip()
                if val:
                    params[param_key] = val

            elif ftype == "date_range":
                d_from = w._d_from.date().toString("yyyy-MM-dd")
                d_to = w._d_to.date().toString("yyyy-MM-dd")
                params[param_key] = f"{d_from}|{d_to}"

            elif ftype == "select":
                val = w.currentData()
                if val:
                    params[param_key] = val

        return params

    def _on_filter_search(self) -> None:
        self._reload_fresh()

    # ── Show ─────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
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
        self._current_page = 0
        self._total_count = 0
        self._all_rows = []
        self._load_next_page()

    def _load_next_page(self) -> None:
        if not self._current_agent_id or self._is_loading:
            return
        if self._current_page > 0 and len(self._all_rows) >= self._total_count:
            return

        self._is_loading = True
        aid = self._current_agent_id
        params = self._get_search_params()
        page = self._current_page + 1

        run_in_thread(
            lambda: self._fetch_upstream(aid, page, PAGE_SIZE, **params),
            on_result=lambda data: self._on_page_data(data, page),
            on_error=self._on_error,
            on_finished=self._on_load_finished,
        )
        if self._current_page == 0:
            self._loading.start(t("loading.loading_data"))

    def _fetch_upstream(self, agent_id: int, page: int, limit: int,
                        **params) -> dict:
        """Override in subclass."""
        raise NotImplementedError

    def _formatters(self) -> dict:
        """Override to provide column formatters. Default: no formatting."""
        return {}

    def _on_page_data(self, data: dict, page: int) -> None:
        rows = data.get("data", [])
        self._total_count = data.get("count", 0)
        self._current_page = page

        if page == 1:
            self._all_rows = rows
            self._render_table(self._all_rows)
        else:
            self._all_rows.extend(rows)
            self._append_rows(rows)

        self.crud.set_total(self._total_count, reset_page=False)
        if self.crud._pager:
            self.crud._pager._current = page
            self.crud._pager._refresh()

    def _render_table(self, rows: list[dict]) -> None:
        keys = [ck[1] for ck in self._columns_keys]
        self.crud.load(rows, keys=keys, id_key="id", formatters=self._formatters())

    def _append_rows(self, rows: list[dict]) -> None:
        keys = [ck[1] for ck in self._columns_keys]
        fmts = self._formatters()
        table = self.crud.table
        center = Qt.AlignmentFlag.AlignCenter
        start_row = table.rowCount()

        table.setUpdatesEnabled(False)
        table.setRowCount(start_row + len(rows))

        for i, rec in enumerate(rows):
            row = start_row + i
            for col, key in enumerate(keys):
                val = rec.get(key, "")
                if key in fmts:
                    display = fmts[key](val)
                else:
                    display = str(val) if val is not None else ""
                item = QTableWidgetItem(display)
                item.setTextAlignment(center)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, rec.get("id"))
                table.setItem(row, col, item)

        table.setUpdatesEnabled(True)

    def _on_jump_data(self, data: dict, page: int) -> None:
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

    # ── Infinite scroll ──────────────────────────────────────

    def _on_scroll(self, value: int) -> None:
        sb = self._scrollbar
        if sb.maximum() == 0:
            return
        remaining = sb.maximum() - value
        threshold = max(50, self.crud.table.viewport().height() // 5)
        if remaining <= threshold:
            self._load_next_page()

    # ── Pagination ───────────────────────────────────────────

    def _on_page(self, page: int) -> None:
        if self._is_loading:
            return
        self._current_page = page - 1
        self._all_rows = []
        self._is_loading = True
        aid = self._current_agent_id
        params = self._get_search_params()

        run_in_thread(
            lambda: self._fetch_upstream(aid, page, PAGE_SIZE, **params),
            on_result=lambda data: self._on_jump_data(data, page),
            on_error=self._on_error,
            on_finished=self._on_load_finished,
        )
        self._loading.start(t("loading.loading_data"))

    # ── Public ───────────────────────────────────────────────

    def refresh_agents(self) -> None:
        agents = upstream.get_agents_local()
        if agents:
            self._apply_agents(agents)

    # ── Retranslate ──────────────────────────────────────────

    def retranslate(self) -> None:
        self._title_lbl.setText(t(self._title_key))
        self._agent_label.setText(t("customer.agent_select"))
        columns = [t(ck[0]) for ck in self._columns_keys]
        self.crud.table.setHorizontalHeaderLabels(columns)

        # Retranslate filter labels
        for field in self._search_fields:
            key = field["key"]
            if key in self._filter_labels:
                self._filter_labels[key].setText(t(field["label"]))
            w = self._filter_widgets.get(key)
            if w and field.get("type") == "text":
                w.setPlaceholderText(t(field.get("placeholder", "crud.search")))
            elif w and field.get("type") == "select":
                for i, (opt_label, _) in enumerate(field.get("options", [])):
                    w.setItemText(i, t(opt_label))

        if hasattr(self, "_btn_search"):
            self._btn_search.setText(t("crud.search"))
