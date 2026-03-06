"""
core/app_window.py — Main window cua ung dung
Chua: MenuBar, ToolBar, CollapsibleSidebar + QStackedWidget
"""
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget,
    QToolBar, QHBoxLayout, QMessageBox, QProgressDialog,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from core import theme
from core.base_widgets import vbox
from utils.settings import settings
from widgets.sidebar import CollapsibleSidebar

logger = logging.getLogger(__name__)

# Import cac tab cua du an
from tabs.home_tab    import HomeTab
from tabs.example_tab import ExampleTab


# ── Menu config — them/xoa/reorder tai day ────────────────────────────────────
# Moi entry: {"icon": "<path>.svg", "text": "Ten hien thi", "tab": TabClass}
# Icon sources: icons/layui/, icons/material/, icons/gallery/
# None = separator
MENU: list[dict | None] = [
    {"icon": "icons/layui/home.svg",            "text": "Trang chu", "tab": HomeTab},
    None,  # separator
    {"icon": "icons/gallery/Grid_black.svg",    "text": "Vi du",     "tab": ExampleTab},
    # Them muc moi:
    # {"icon": "icons/layui/user.svg",  "text": "Nhan vien", "tab": NhanVienTab},
    # {"icon": "icons/layui/set.svg",   "text": "Cai dat",   "tab": CaiDatTab},
]


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.setMinimumSize(theme.WINDOW_MIN_W, theme.WINDOW_MIN_H)

        self._build_central()
        self._build_toolbar()   # after _build_central so self._sidebar exists

    # ── Lifecycle ─────────────────────────────────────────

    def show(self):
        super().show()
        settings.restore_window(self)
        self._check_for_updates()

    def closeEvent(self, event):
        settings.save_window(self)
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

        from utils.updater import APP_VERSION
        version = info["version"]
        force = info.get("force", False)

        if force:
            buttons = QMessageBox.StandardButton.Ok
        else:
            buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

        msg = (
            f"Phien ban moi {version} da san sang!\n"
            f"(Hien tai: {APP_VERSION})\n\n"
            "Ban co muon cap nhat ngay?"
        )
        reply = QMessageBox.question(
            self, "Cap nhat phan mem", msg, buttons,
        )

        if force or reply == QMessageBox.StandardButton.Yes:
            self._start_download(info["update_url"])

    def _start_download(self, url: str) -> None:
        from utils.thread_worker import Worker
        from utils.updater import download_update

        self._progress = QProgressDialog(
            "Dang tai ban cap nhat...", "Huy", 0, 100, self
        )
        self._progress.setWindowTitle("Cap nhat")
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.setValue(0)

        worker = Worker(download_update, url, use_progress=True)
        worker.signals.progress.connect(self._progress.setValue)
        worker.signals.result.connect(self._on_download_done)
        worker.signals.error.connect(self._on_download_error)
        self._update_worker = worker
        worker.start()

    def _on_download_done(self, exe_path: str) -> None:
        self._progress.close()
        reply = QMessageBox.information(
            self,
            "Cap nhat",
            "Tai ban cap nhat thanh cong!\n"
            "Ung dung se khoi dong lai de hoan tat.",
            QMessageBox.StandardButton.Ok,
        )
        from utils.updater import apply_update
        apply_update(exe_path)

    def _on_download_error(self, err: str) -> None:
        self._progress.close()
        logger.error("Download update failed: %s", err)
        QMessageBox.warning(
            self, "Loi cap nhat",
            "Khong the tai ban cap nhat.\nVui long thu lai sau.",
        )

    # ── Toolbar ───────────────────────────────────────────

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        # Toggle sidebar giờ nằm trong sidebar — giữ shortcut ở đây
        act_toggle = QAction(self)
        act_toggle.setShortcut("Ctrl+\\")
        act_toggle.triggered.connect(self._sidebar.toggle)
        self.addAction(act_toggle)

        tooltips = {
            "New": "Tao moi (Ctrl+N)",
            "Open": "Mo file (Ctrl+O)",
            "Save": "Luu file (Ctrl+S)",
            "Undo": "Hoan tac (Ctrl+Z)",
            "Redo": "Lam lai (Ctrl+Y)",
        }
        for label in ["New", "Open", "Save", "|", "Undo", "Redo"]:
            if label == "|":
                tb.addSeparator()
            else:
                act = QAction(label, self)
                act.setToolTip(tooltips.get(label, label))
                tb.addAction(act)

    # ── Central ───────────────────────────────────────────

    def _build_central(self) -> None:
        self._stack   = QStackedWidget()
        self._sidebar = CollapsibleSidebar()

        for item in MENU:
            if item is None:
                self._sidebar.add_separator()
            else:
                page = item["tab"]()
                self._stack.addWidget(page)
                self._sidebar.add_item(item["icon"], item["text"], page)

        self._sidebar.page_changed.connect(self._stack.setCurrentWidget)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(*theme.MARGIN_ZERO)
        lay.setSpacing(0)
        lay.addWidget(self._sidebar)
        lay.addWidget(self._stack, 1)
        self.setCentralWidget(central)

