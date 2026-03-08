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
    QComboBox, QTableWidgetItem, QLineEdit,
    QPushButton, QLabel, QWidget, QVBoxLayout,
)
from PyQt6.QtCore import Qt, QSize, QTimer
from core.base_widgets import BaseTab, label, divider, hbox
from core import theme
from core.i18n import t
from core.icon import Icon, IconPath
from core.theme import tinted_icon, theme_signals
from utils.upstream import upstream
from utils.formatters import currency
from utils.thread_worker import run_in_thread
from utils.ws_client import ws_client
from widgets.table_crud import TableCrud
from widgets.loading import LoadingOverlay
from widgets.error_state import ErrorState
from widgets.date_range_picker import DateRangePicker
from widgets.stat_card import StatCard
from dialogs.confirm_dialog import error

import math

PAGE_SIZE = 100
EXPORT_PAGE_SIZE = 2000


def _fmt_currency(v) -> str:
    """Safely format upstream monetary values (may contain commas, e.g. '39,810.1500')."""
    if not v and v != 0:
        return "0"
    try:
        return currency(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return str(v)


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
    _prefix_key: str = "upstream.prefix"
    _columns_keys: list[tuple[str, str]] = []
    _search_fields: list[dict] = []
    _summary_keys: list[tuple[str, str]] = []  # [(i18n_key, data_key), ...]
    _data_type: str = ""  # cache key cho group sync (e.g. "customers", "lottery")

    def _build(self, layout) -> None:
        # Title + Summary cards trên cùng 1 dòng
        title_row = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)

        # Two-line centered title (prefix + subtitle)
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title_col.setContentsMargins(0, 0, 0, 0)

        if self._prefix_key:
            self._prefix_lbl = label(t(self._prefix_key), size=theme.FONT_SIZE)
            self._prefix_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_col.addWidget(self._prefix_lbl)
        else:
            self._prefix_lbl = None

        self._title_lbl = label(t(self._title_key), bold=True, size=theme.FONT_SIZE_LG)
        if self._prefix_key:
            self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_col.addWidget(self._title_lbl)
        title_row.addLayout(title_col)

        self._summary_cards: list[tuple[str, str, StatCard]] = []
        if self._summary_keys:
            for i18n_key, data_key in self._summary_keys:
                card = StatCard(t(i18n_key), "0",
                                min_width=80, value_size=theme.FONT_SIZE_LG)
                self._summary_cards.append((i18n_key, data_key, card))
                title_row.addWidget(card, 1)

        self._build_extra_cards(title_row)
        layout.addLayout(title_row)

        layout.addWidget(divider())

        # Agent + Group selector row
        agent_row = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        self._agent_label = label(t("customer.agent_select"))
        agent_row.addWidget(self._agent_label)
        self._agent_combo = QComboBox()
        self._agent_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._agent_combo.currentIndexChanged.connect(self._on_agent_changed)
        agent_row.addWidget(self._agent_combo)

        agent_row.addSpacing(theme.SPACING_LG)

        # Group selector
        self._group_label = label(t("group.select"))
        agent_row.addWidget(self._group_label)
        self._group_combo = QComboBox()
        self._group_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._group_combo.addItem(t("group.none"), None)
        self._group_combo.currentIndexChanged.connect(self._on_group_changed)
        agent_row.addWidget(self._group_combo)

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
        self.crud._toolbar.hide()
        layout.addWidget(self.crud)

        # Error state (hidden by default)
        self._error_state: ErrorState | None = None
        self._error_layout = layout

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

        # Group mode state
        self._groups: list[dict] = []
        self._current_group_id: int | None = None
        self._group_mode = False
        self._cache_version = 0
        self._poll_timer: QTimer | None = None

        # WebSocket listener cho group mode
        ws_client.data_updated.connect(self._on_ws_data_updated)

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
                ph = t(field.get("placeholder", "crud.search"))
                w.setPlaceholderText(ph)
                # Width based on placeholder text length
                fm = w.fontMetrics()
                w.setMinimumWidth(fm.horizontalAdvance(ph) + 24)
                w.returnPressed.connect(self._on_filter_search)
                row.addWidget(w)

            elif ftype == "date_range":
                default = field.get("default", "")
                if default == "today":
                    from PyQt6.QtCore import QDate
                    today = QDate.currentDate()
                    w = DateRangePicker(
                        d_from=today, d_to=today,
                        optional=field.get("optional", False),
                    )
                else:
                    w = DateRangePicker(optional=field.get("optional", False))
                w.range_changed.connect(lambda *_: self._on_filter_search())
                row.addWidget(w)

            elif ftype == "select":
                w = QComboBox()
                for opt_label, opt_val in field.get("options", []):
                    w.addItem(t(opt_label), opt_val)
                w.setSizeAdjustPolicy(
                    QComboBox.SizeAdjustPolicy.AdjustToContents)
                w.setMaxVisibleItems(20)
                row.addWidget(w)

            self._filter_widgets[key] = w

        # Search button
        _ico = QSize(15, 15)
        self._btn_search = QPushButton(tinted_icon(IconPath.SEARCH, size=15), t("crud.search"))
        self._btn_search.setIconSize(_ico)
        self._btn_search.clicked.connect(self._on_filter_search)
        row.addWidget(self._btn_search)

        # Reset button
        self._btn_reset = QPushButton(tinted_icon(IconPath.REFRESH, size=15), t("crud.reset"))
        self._btn_reset.setIconSize(_ico)
        self._btn_reset.clicked.connect(self._on_filter_reset)
        row.addWidget(self._btn_reset)

        # Refresh icons on theme change
        theme_signals.changed.connect(self._on_filter_theme_changed)

        # Export button
        row.addStretch()
        self._btn_export = QPushButton(tinted_icon(IconPath.EXPORT, size=15), t("crud.export"))
        self._btn_export.setIconSize(_ico)
        self._btn_export.clicked.connect(self._on_export)
        row.addWidget(self._btn_export)

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
                params[param_key] = w.text().strip()

            elif ftype == "date_range":
                params[param_key] = w.text()

            elif ftype == "select":
                params[param_key] = w.currentData() or ""

        return params

    def _on_filter_search(self) -> None:
        self._reload_fresh()

    def _on_filter_reset(self) -> None:
        """Reset all filter widgets to default values."""
        for field in self._search_fields:
            key = field["key"]
            w = self._filter_widgets.get(key)
            if not w:
                continue
            ftype = field.get("type", "text")
            if ftype == "text":
                w.clear()
            elif ftype == "date_range":
                w.reset()
            elif ftype == "select":
                w.setCurrentIndex(0)
        self._reload_fresh()

    def _on_export(self) -> None:
        """Xuất toàn bộ dữ liệu (tất cả page) ra Excel."""
        if not self._current_agent_id:
            return
        if self._is_loading:
            return

        self._btn_export.setEnabled(False)
        self._export_all_rows: list[dict] = []
        self._export_total = 0
        self._export_page = 0
        self._fetch_export_page()

    def _fetch_export_page(self) -> None:
        aid = self._current_agent_id
        params = self._get_search_params()
        page = self._export_page + 1
        total_display = self._export_total or "..."

        run_in_thread(
            lambda: self._fetch_upstream(aid, page, EXPORT_PAGE_SIZE, **params),
            on_result=lambda data: self._on_export_page(data, page),
            on_error=self._on_export_error,
        )
        self._loading.start(
            t("crud.exporting",
              current=len(self._export_all_rows), total=total_display))

    def _on_export_page(self, data: dict, page: int) -> None:
        rows = data.get("data", [])
        self._export_total = data.get("count", 0)
        self._export_page = page
        self._export_all_rows.extend(rows)

        loaded = len(self._export_all_rows)
        total_pages = math.ceil(
            self._export_total / EXPORT_PAGE_SIZE) if self._export_total else 1

        # Cập nhật progress ngay với số thực tế
        self._loading._loading_label.setText(
            t("crud.exporting", current=loaded, total=self._export_total))

        if loaded < self._export_total and page < total_pages:
            self._fetch_export_page()
        else:
            self._loading.stop()
            self._btn_export.setEnabled(True)
            self._do_export_data()

    def _on_export_error(self, exc: Exception) -> None:
        self._btn_export.setEnabled(True)
        self._export_all_rows = []
        self._loading.notify("error", t("crud.export_error"))

    def _do_export_data(self) -> None:
        from utils.export_table import export_data

        headers = [t(ck[0]) for ck in self._columns_keys]
        keys = [ck[1] for ck in self._columns_keys]
        default_name = self._build_export_filename()

        ok = export_data(
            self.window(), headers, self._export_all_rows,
            keys, self._formatters(), default_name,
        )
        self._export_all_rows = []
        if ok:
            self._loading.notify("success", t("crud.export_success"))
        elif ok is False:
            self._loading.notify("error", t("crud.export_error"))

    def _build_export_filename(self) -> str:
        """Tạo tên file mặc định: 'Title - dd.MM - dd.MM.xlsx'."""
        title = f"{t(self._prefix_key)} {t(self._title_key)}" if self._prefix_key else t(self._title_key)
        date_part = ""
        for field in self._search_fields:
            if field.get("type") == "date_range":
                w = self._filter_widgets.get(field["key"])
                if w and w.date_from() and w.date_to():
                    d_from = w.date_from().toString("dd.MM")
                    d_to = w.date_to().toString("dd.MM")
                    if d_from == d_to:
                        date_part = f" - {d_from}"
                    else:
                        date_part = f" - {d_from} - {d_to}"
                break
        return f"{title}{date_part}.xlsx"

    def _on_filter_theme_changed(self, _dark: bool) -> None:
        self._btn_search.setIcon(tinted_icon(IconPath.SEARCH, size=15))
        self._btn_reset.setIcon(tinted_icon(IconPath.REFRESH, size=15))
        if hasattr(self, "_btn_export"):
            self._btn_export.setIcon(tinted_icon(IconPath.EXPORT, size=15))

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
            # Load groups list (background)
            self._load_groups()

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
        if self._group_mode:
            return  # Ignore agent changes in group mode
        self._current_agent_id = self._agent_combo.currentData()
        if self._current_agent_id:
            self._reload_fresh()

    # ── Group mode ────────────────────────────────────────────

    def _load_groups(self) -> None:
        """Load groups from server (background)."""
        from utils.api import api
        run_in_thread(
            lambda: api.get("/api/groups"),
            on_result=self._on_groups_loaded,
        )

    def _on_groups_loaded(self, result) -> None:
        ok, data = result
        if not ok or not data.get("ok"):
            return
        self._groups = data.get("groups", [])
        self._group_combo.blockSignals(True)
        self._group_combo.clear()
        self._group_combo.addItem(t("group.none"), None)
        for g in self._groups:
            self._group_combo.addItem(g["name"], g["id"])
        self._group_combo.blockSignals(False)

    def _on_group_changed(self, index: int) -> None:
        group_id = self._group_combo.currentData()
        self._stop_polling()

        if group_id is None:
            # Switch back to agent mode
            self._group_mode = False
            self._current_group_id = None
            self._agent_combo.setEnabled(True)
            if self._current_agent_id:
                self._reload_fresh()
            return

        # Switch to group mode
        self._group_mode = True
        self._current_group_id = group_id
        self._agent_combo.setEnabled(False)
        self._load_group_data()

    def _load_group_data(self) -> None:
        """Load group data — try cache first, fallback to parallel fetch."""
        if not self._current_group_id or not self._data_type:
            return
        from utils.api import api
        gid = self._current_group_id
        self._loading.start(t("loading.loading_data"))

        run_in_thread(
            lambda: api.get(f"/api/groups/{gid}/cache?data_type={self._data_type}"),
            on_result=self._on_cache_result,
            on_error=lambda e: self._fetch_and_sync(),
        )

    def _on_cache_result(self, result) -> None:
        ok, data = result
        if ok and data.get("ok"):
            synced_at = data.get("synced_at", "")
            if self._is_cache_stale(synced_at, max_age_seconds=300):
                self._fetch_and_sync()
            else:
                self._render_group_result(data)
                self._cache_version = data.get("version", 0)
                self._loading.stop()
                self._start_polling()
        else:
            self._fetch_and_sync()

    def _is_cache_stale(self, synced_at: str, max_age_seconds: int = 300) -> bool:
        """Check if cache is older than max_age_seconds."""
        if not synced_at:
            return True
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(synced_at)
            age = (datetime.now(timezone.utc) - dt).total_seconds()
            return age > max_age_seconds
        except (ValueError, TypeError):
            return True

    def _fetch_and_sync(self) -> None:
        """Fetch directly from all group agents → display → push to server."""
        if not self._current_group_id or not self._data_type:
            self._loading.stop()
            return

        gid = self._current_group_id
        self._loading.start(t("group.fetching_agents"))

        # First, get group agents with cookies from server
        from utils.api import api
        run_in_thread(
            lambda: api.get(f"/api/groups/{gid}/agents"),
            on_result=self._on_group_agents_for_fetch,
            on_error=lambda e: self._on_group_fetch_error(e),
        )

    def _on_group_agents_for_fetch(self, result) -> None:
        ok, data = result
        if not ok or not data.get("ok"):
            self._loading.stop()
            return

        agents = data.get("agents", [])
        if not agents:
            self._loading.stop()
            return

        gid = self._current_group_id
        # Cache group agents + cookies locally
        upstream.save_group_agents_local(gid, agents)

        # Filter only active agents with cookies
        active_agents = [a for a in agents if a.get("session_cookie")]
        if not active_agents:
            self._loading.stop()
            return

        # Build upstream path + params for this tab
        path, extra = self._get_upstream_path_and_params()

        self._loading.start(t("group.fetching_data"))

        run_in_thread(
            lambda: upstream.parallel_fetch(
                active_agents, path, page=1, limit=2000,
                extra_params=extra,
            ),
            on_result=self._on_parallel_done,
            on_error=lambda e: self._on_group_fetch_error(e),
        )

    def _on_parallel_done(self, result) -> None:
        # 1. Display immediately
        self._render_group_result(result)
        self._loading.stop()

        # 2. Push to server cache (background)
        if self._current_group_id and self._data_type:
            from utils.api import api
            gid = self._current_group_id
            run_in_thread(
                lambda: api.post(f"/api/groups/{gid}/sync", {
                    "data_type": self._data_type,
                    "data": result.get("data", []),
                    "agents_fetched": result.get("agents_fetched", []),
                    "agents_errors": result.get("agents_errors", []),
                }),
                on_result=self._on_sync_done,
            )

        self._start_polling()

    def _on_sync_done(self, result) -> None:
        ok, data = result
        if ok and data.get("ok"):
            self._cache_version = data.get("version", 0)

    def _render_group_result(self, data: dict) -> None:
        """Render group data (from cache or parallel fetch)."""
        rows = data.get("data", [])
        self._all_rows = rows
        self._total_count = data.get("total_count", data.get("count", len(rows)))
        self._current_page = 1
        self._render_table(rows)
        self.crud.set_total(self._total_count, reset_page=False)
        self._update_summary()

    def _on_group_fetch_error(self, exc) -> None:
        self._loading.stop()
        self._is_loading = False

    def _get_upstream_path_and_params(self) -> tuple[str, str]:
        """Return (path, extra_params) for upstream fetch.
        Override in subclass if needed, default: derive from _fetch_upstream."""
        # Build search params
        params = self._get_search_params()
        extra = "&".join(f"{k}={v}" for k, v in params.items() if v)
        # Path is determined by _data_type mapping
        path_map = {
            "customers": "/agent/user.html",
            "deposits": "/agent/depositAndWithdrawal.html",
            "withdrawals": "/agent/withdrawalsRecord.html",
            "transactions": "/agent/reportFunds.html",
            "bet_lottery": "/agent/bet.html",
            "bet_provider": "/agent/betOrder.html",
            "lottery": "/agent/reportLottery.html",
            "provider": "/agent/reportThirdGame.html",
            "referrals": "/agent/inviteList.html",
        }
        path = path_map.get(self._data_type, "")
        # Some paths need extra default params
        if self._data_type == "customers":
            extra = f"hs_search=true&{extra}" if extra else "hs_search=true"
        elif self._data_type == "bet_lottery":
            extra = f"es=1&is_summary=0&{extra}" if extra else "es=1&is_summary=0"
        elif self._data_type == "bet_provider":
            extra = f"es=1&{extra}" if extra else "es=1"
        return path, extra

    # ── Polling ───────────────────────────────────────────────

    def _start_polling(self) -> None:
        """Start 30s polling as fallback when WS not connected."""
        self._stop_polling()
        if not self._group_mode or not self._current_group_id:
            return
        # WS connected → realtime via _on_ws_data_updated, no polling needed
        if ws_client.is_connected:
            return
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(30_000)
        self._poll_timer.timeout.connect(self._check_version)
        self._poll_timer.start()

    def _stop_polling(self) -> None:
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer.deleteLater()
            self._poll_timer = None

    def _check_version(self) -> None:
        """Lightweight poll — only check version number."""
        if not self._current_group_id or not self._data_type:
            return
        from utils.api import api
        gid = self._current_group_id
        dt = self._data_type
        run_in_thread(
            lambda: api.get(f"/api/groups/{gid}/cache/version?data_type={dt}"),
            on_result=self._on_version_check,
        )

    def _on_version_check(self, result) -> None:
        ok, data = result
        if ok and data.get("version", 0) > self._cache_version:
            self._load_group_data()

    # ── WebSocket realtime ────────────────────────────────────

    def _on_ws_data_updated(self, event: dict) -> None:
        """Data nhom duoc member khac cap nhat -> reload cache."""
        if not self._group_mode:
            return
        if event.get("group_id") != self._current_group_id:
            return
        if event.get("data_type") != self._data_type:
            return
        from utils.api import api
        if event.get("synced_by") == api.username:
            # Chinh minh sync — chi cap nhat version, khong reload
            self._cache_version = event.get("version", self._cache_version)
            return
        # Member khac sync — reload cache moi
        new_ver = event.get("version", 0)
        if new_ver > self._cache_version:
            self._load_group_data()

    # ── Data loading (infinite scroll) ───────────────────────

    def _reload_fresh(self) -> None:
        self._hide_error_state()
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

    # Các data_key mang ý nghĩa thắng/thua — tô màu theo giá trị
    _win_lose_keys: set[str] = {"result", "win_lose", "t_win_lose"}

    def _update_summary(self) -> None:
        """Tính tổng các cột trong _summary_keys từ _all_rows và cập nhật StatCard."""
        if not self._summary_cards:
            return
        for i18n_key, data_key, card in self._summary_cards:
            total = 0.0
            for row in self._all_rows:
                val = row.get(data_key, 0)
                try:
                    total += float(str(val).replace(",", "")) if val else 0
                except (TypeError, ValueError):
                    pass
            card.update_value(_fmt_currency(total))
            if data_key in self._win_lose_keys:
                if total > 0:
                    card.set_value_color("#4caf50")
                elif total < 0:
                    card.set_value_color("#f44336")
                else:
                    card.set_value_color("")
        self._update_extra_cards()

    def _build_extra_cards(self, title_row) -> None:
        """Hook: subclass adds extra cards to title_row."""

    def _update_extra_cards(self) -> None:
        """Hook: subclass updates extra cards from _all_rows."""

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
        self._update_summary()

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
        self._update_summary()

    def _on_load_finished(self) -> None:
        self._is_loading = False
        self._loading.stop()

    def _on_error(self, exc: Exception) -> None:
        code = self._parse_error_code(exc)
        self._show_error_state(code, exc)

    @staticmethod
    def _parse_error_code(exc: Exception) -> int:
        """Extract HTTP error code from exception message."""
        msg = str(exc)
        if isinstance(exc, PermissionError) or "session" in msg.lower():
            return 401
        if "403" in msg:
            return 403
        if "404" in msg:
            return 404
        if isinstance(exc, ValueError):
            return 401
        return 500

    def _show_error_state(self, code: int, exc: Exception | None = None) -> None:
        """Show error page with SVG illustration, hide table."""
        self._hide_error_state()
        self.crud.hide()

        title = t(f"error_state.title_{code}")
        desc = t(f"error_state.desc_{code}")
        self._error_state = ErrorState(
            code=code, title=title, description=desc,
            on_retry=self._on_retry,
        )
        self._error_layout.addWidget(self._error_state)

    def _hide_error_state(self) -> None:
        """Remove error state and show table again."""
        if self._error_state:
            self._error_state.setParent(None)
            self._error_state.deleteLater()
            self._error_state = None
        self.crud.show()

    def _on_retry(self) -> None:
        """Retry loading data — hide error state and reload."""
        self._hide_error_state()
        self._reload_fresh()

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

    def closeEvent(self, event) -> None:
        self._stop_polling()
        try:
            ws_client.data_updated.disconnect(self._on_ws_data_updated)
        except TypeError:
            pass
        super().closeEvent(event)

    def retranslate(self) -> None:
        self._title_lbl.setText(t(self._title_key))
        if self._prefix_lbl:
            self._prefix_lbl.setText(t(self._prefix_key))
        for i18n_key, _data_key, card in self._summary_cards:
            card.set_title(t(i18n_key))
        self._agent_label.setText(t("customer.agent_select"))
        self._group_label.setText(t("group.select"))
        # Retranslate group combo first item
        if self._group_combo.count() > 0:
            self._group_combo.setItemText(0, t("group.none"))
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
        if hasattr(self, "_btn_reset"):
            self._btn_reset.setText(t("crud.reset"))
        if hasattr(self, "_btn_export"):
            self._btn_export.setText(t("crud.export"))
