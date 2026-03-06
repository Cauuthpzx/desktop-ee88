"""
core/app_window.py — Main window cua ung dung
Chua: MenuBar, ToolBar, CollapsibleSidebar + QStackedWidget
"""
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QSizePolicy,
    QToolBar, QHBoxLayout,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from core import theme
from core.i18n import t, i18n_signals
from core.theme import theme_signals
from core.base_widgets import vbox
from utils.settings import settings
from widgets.sidebar import CollapsibleSidebar

logger = logging.getLogger(__name__)

# Import cac tab cua du an
from tabs.home_tab     import HomeTab
from tabs.example_tab  import ExampleTab
from tabs.account_tab  import AccountTab
from tabs.settings_tab import SettingsTab


# ── Menu config — them/xoa/reorder tai day ────────────────────────────────────
# Moi entry: {"icon": "<path>.svg", "text_key": "sidebar.xxx", "tab": TabClass}
# Icon sources: icons/layui/, icons/material/, icons/gallery/
# None = separator
MENU: list[dict | None] = [
    {"icon": "icons/layui/home.svg",            "text_key": "sidebar.home",    "tab": HomeTab},
    None,  # separator
    {"icon": "icons/gallery/Grid_black.svg",    "text_key": "sidebar.example",  "tab": ExampleTab},
]

# Items ghim dưới cùng sidebar
MENU_BOTTOM: list[dict] = [
    {"icon": "icons/layui/user.svg", "text_key": "sidebar.account",  "tab": AccountTab},
    {"icon": "icons/layui/set.svg",  "text_key": "sidebar.settings", "tab": SettingsTab},
]


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app.title"))
        self.setMinimumSize(theme.WINDOW_MIN_W, theme.WINDOW_MIN_H)

        self._build_central()
        self._build_toolbar()   # after _build_central so self._sidebar exists

        i18n_signals.language_changed.connect(self._retranslate)

    # ── Lifecycle ─────────────────────────────────────────

    def show(self):
        super().show()
        settings.restore_window(self)
        self._check_for_updates()

    def closeEvent(self, event):
        settings.save_window(self)
        i18n_signals.language_changed.disconnect(self._retranslate)
        theme_signals.changed.disconnect(self._on_theme_changed)
        self._sidebar.cleanup()
        super().closeEvent(event)

    # ── Auto Update ────────────────────────────────────────

    def _check_for_updates(self) -> None:
        from utils.thread_worker import run_in_thread
        from utils.updater import check_update

        run_in_thread(
            check_update,
            on_result=self._on_update_check,
            on_error=lambda e: logger.debug("Update check failed: %s", e),
        )

    def _on_update_check(self, info: dict | None) -> None:
        if not info:
            return
        from dialogs.update_dialog import UpdateDialog
        dlg = UpdateDialog(self, info)
        dlg.exec()

    # ── Toolbar ───────────────────────────────────────────

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Toggle sidebar — shortcut
        act_toggle = QAction(self)
        act_toggle.setShortcut("Ctrl+\\")
        act_toggle.triggered.connect(self._sidebar.toggle)
        self.addAction(act_toggle)

        tooltips = {
            "New": t("toolbar.tip_new"),
            "Open": t("toolbar.tip_open"),
            "Save": t("toolbar.tip_save"),
            "Undo": t("toolbar.tip_undo"),
            "Redo": t("toolbar.tip_redo"),
        }
        for lbl in ["New", "Open", "Save", "|", "Undo", "Redo"]:
            if lbl == "|":
                tb.addSeparator()
            else:
                act = QAction(lbl, self)
                act.setToolTip(tooltips.get(lbl, lbl))
                tb.addAction(act)

        # Spacer — đẩy theme toggle sang phải
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        # Theme toggle button — top-right
        self._act_theme = QAction(self)
        self._update_theme_icon()
        self._act_theme.setToolTip(t("settings.theme_toggle"))
        self._act_theme.triggered.connect(self._on_toggle_theme)
        tb.addAction(self._act_theme)
        theme_signals.changed.connect(self._on_theme_changed)

    def _update_theme_icon(self) -> None:
        if theme.is_dark():
            self._act_theme.setIcon(theme.tinted_icon("icons/material/light_mode.svg"))
        else:
            self._act_theme.setIcon(theme.tinted_icon("icons/material/dark_mode.svg"))

    def _on_theme_changed(self, _dark: bool) -> None:
        self._update_theme_icon()

    def _on_toggle_theme(self) -> None:
        theme.toggle_theme()

    # ── Central ───────────────────────────────────────────

    def _build_central(self) -> None:
        self._stack   = QStackedWidget()
        self._sidebar = CollapsibleSidebar()
        self._pages: list[tuple[QWidget, str]] = []  # (page, text_key)

        for item in MENU:
            if item is None:
                self._sidebar.add_separator()
            else:
                page = item["tab"]()
                self._stack.addWidget(page)
                self._sidebar.add_item(item["icon"], t(item["text_key"]), page)
                self._pages.append((page, item["text_key"]))

        for item in MENU_BOTTOM:
            page = item["tab"]()
            self._stack.addWidget(page)
            self._sidebar.add_item_bottom(item["icon"], t(item["text_key"]), page)
            self._pages.append((page, item["text_key"]))

        self._sidebar.page_changed.connect(self._stack.setCurrentWidget)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(*theme.MARGIN_ZERO)
        lay.setSpacing(0)
        lay.addWidget(self._sidebar)
        lay.addWidget(self._stack, 1)
        self.setCentralWidget(central)

    def _retranslate(self, _lang: str = "") -> None:
        """Update all UI text when language changes."""
        self.setWindowTitle(t("app.title"))
        self._act_theme.setToolTip(t("settings.theme_toggle"))

        # Sidebar nav texts
        text_map = {page: t(key) for page, key in self._pages}
        self._sidebar.update_texts(text_map)

        # Retranslate each tab that supports it
        for i in range(self._stack.count()):
            page = self._stack.widget(i)
            if hasattr(page, "retranslate"):
                page.retranslate()
