"""
core/app_window.py — Main window cua ung dung
Chua: MenuBar, ToolBar, CollapsibleSidebar + QStackedWidget
"""
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QSizePolicy,
    QToolBar, QHBoxLayout, QTabBar,
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt
from core import theme
from core.icon import Icon, IconPath, GalleryIcon, tinted
from core.i18n import t, i18n_signals
from core.theme import theme_signals
from core.base_widgets import vbox
from utils.settings import settings
from widgets.sidebar import CollapsibleSidebar
from widgets.notification_bell import NotificationBell

logger = logging.getLogger(__name__)

# Import cac tab cua du an
from tabs.home_tab        import HomeTab
from tabs.customer_tab    import CustomerTab
from tabs.referral_tab    import ReferralTab
from tabs.lottery_tab     import LotteryTab
from tabs.transaction_tab import TransactionTab
from tabs.provider_tab    import ProviderTab
from tabs.deposit_tab     import DepositTab
from tabs.withdraw_tab    import WithdrawTab
from tabs.bet_lottery_tab  import BetLotteryTab
from tabs.bet_provider_tab import BetProviderTab
from tabs.account_tab     import AccountTab
from tabs.settings_tab    import SettingsTab


# ── Menu config — them/xoa/reorder tai day ────────────────────────────────────
# Moi entry: {"icon": "<path>.svg", "text_key": "sidebar.xxx", "tab": TabClass}
# Group entry: {"icon": ..., "text_key": ..., "children": [child items]}
# Icon sources: icons/layui/, icons/material/, icons/gallery/
# None = separator
MENU: list[dict | None] = [
    {"icon": IconPath.HOME,                        "text_key": "sidebar.home",     "tab": HomeTab},
    None,  # separator
    {"icon": IconPath.GROUPS,                      "text_key": "sidebar.customer", "tab": CustomerTab},
    {"icon": IconPath.TEMPLATE,                    "text_key": "sidebar.referral", "tab": ReferralTab},
    None,  # separator
    {"icon": IconPath.CASINO, "text_key": "sidebar.game", "children": [
        {"icon": IconPath.CHART,    "text_key": "sidebar.lottery",     "tab": LotteryTab},
        {"icon": IconPath.RECEIPT,  "text_key": "sidebar.transaction", "tab": TransactionTab},
        {"icon": IconPath.STORE,    "text_key": "sidebar.provider",    "tab": ProviderTab},
    ]},
    {"icon": IconPath.LIST_ALT, "text_key": "sidebar.bet_list", "children": [
        {"icon": IconPath.CHART,    "text_key": "sidebar.bet_lottery",  "tab": BetLotteryTab},
        {"icon": IconPath.STORE,    "text_key": "sidebar.bet_provider", "tab": BetProviderTab},
    ]},
    {"icon": IconPath.WALLET, "text_key": "sidebar.deposit_withdraw", "children": [
        {"icon": IconPath.SAVINGS,   "text_key": "sidebar.deposit",  "tab": DepositTab},
        {"icon": IconPath.MONEY_OFF, "text_key": "sidebar.withdraw", "tab": WithdrawTab},
    ]},
]

# Items ghim dưới cùng sidebar
MENU_BOTTOM: list[dict] = [
    {"icon": IconPath.USER,     "text_key": "sidebar.account",  "tab": AccountTab},
    {"icon": IconPath.SETTINGS, "text_key": "sidebar.settings", "tab": SettingsTab},
]


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app.title"))
        self.setMinimumSize(theme.WINDOW_MIN_W, theme.WINDOW_MIN_H)
        self.resize(theme.WINDOW_DEFAULT_W, theme.WINDOW_DEFAULT_H)

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
        self._bell.cleanup()
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

        # Tab bar — chi hien tab header, noi dung hien trong _stack
        self._tab_bar = QTabBar()
        self._tab_bar.setTabsClosable(True)
        self._tab_bar.setMovable(True)
        self._tab_bar.setDocumentMode(True)
        self._tab_bar.setExpanding(False)
        self._tab_bar.tabCloseRequested.connect(self._on_tab_close)
        self._tab_bar.currentChanged.connect(self._on_tab_changed)
        tb.addWidget(self._tab_bar)
        self._tab_pages: list[QWidget] = []  # map tab index -> page widget

        # Spacer — day theme toggle sang phai
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        # Notification bell
        self._bell = NotificationBell()
        tb.addWidget(self._bell)

        # Theme toggle button
        self._act_theme = QAction(self)
        self._update_theme_icon()
        self._act_theme.setToolTip(t("settings.theme_toggle"))
        self._act_theme.triggered.connect(self._on_toggle_theme)
        tb.addAction(self._act_theme)
        theme_signals.changed.connect(self._on_theme_changed)

    # ── Tab management ────────────────────────────────────

    def open_tab(self, page: QWidget, title: str, icon: QIcon | None = None) -> None:
        """Mo tab moi hoac chuyen sang tab da mo neu trung page."""
        for i, pg in enumerate(self._tab_pages):
            if pg is page:
                self._tab_bar.setCurrentIndex(i)
                return
        if self._stack.indexOf(page) == -1:
            self._stack.addWidget(page)
        idx = self._tab_bar.addTab(title)
        if icon:
            self._tab_bar.setTabIcon(idx, icon)
        self._tab_pages.append(page)
        self._tab_bar.setCurrentIndex(idx)

    def _on_tab_close(self, index: int) -> None:
        """Dong tab — khong dong tab cuoi cung."""
        if self._tab_bar.count() <= 1:
            return
        self._tab_bar.removeTab(index)
        self._tab_pages.pop(index)

    def _on_tab_changed(self, index: int) -> None:
        """Chuyen stack theo tab dang chon."""
        if 0 <= index < len(self._tab_pages):
            self._stack.setCurrentWidget(self._tab_pages[index])

    def _update_theme_icon(self) -> None:
        if theme.is_dark():
            self._act_theme.setIcon(tinted(IconPath.LIGHT_MODE))
        else:
            self._act_theme.setIcon(tinted(IconPath.DARK_MODE))

    def _on_theme_changed(self, _dark: bool) -> None:
        self._update_theme_icon()

    def _on_toggle_theme(self) -> None:
        theme.toggle_theme()

    # ── Central ───────────────────────────────────────────

    def _build_central(self) -> None:
        self._stack   = QStackedWidget()
        self._sidebar = CollapsibleSidebar()
        self._pages: list[tuple[QWidget, str]] = []  # (page, text_key)
        self._groups: list[tuple[str, str]] = []      # (group_id, text_key)

        for item in MENU:
            if item is None:
                self._sidebar.add_separator()
            elif "children" in item:
                # Group with children
                grp_id = self._sidebar.add_group(item["icon"], t(item["text_key"]))
                self._groups.append((grp_id, item["text_key"]))
                for child in item["children"]:
                    page = child["tab"]()
                    self._stack.addWidget(page)
                    self._sidebar.add_group_item(grp_id, child["icon"], t(child["text_key"]), page)
                    self._pages.append((page, child["text_key"]))
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
        self._bell.setToolTip(t("notification.title"))

        # Sidebar nav texts
        text_map = {page: t(key) for page, key in self._pages}
        self._sidebar.update_texts(text_map)

        # Sidebar group header texts
        if self._groups:
            grp_map = {grp_id: t(key) for grp_id, key in self._groups}
            self._sidebar.update_group_texts(grp_map)

        # Retranslate each tab that supports it
        for i in range(self._stack.count()):
            page = self._stack.widget(i)
            if hasattr(page, "retranslate"):
                page.retranslate()
