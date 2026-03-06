"""
core/app_window.py — Main window cua ung dung
Chua: MenuBar, ToolBar, CollapsibleSidebar + QStackedWidget
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget,
    QToolBar, QHBoxLayout,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from core import theme
from core.base_widgets import vbox
from dialogs.about_dialog import AboutDialog
from utils.settings import settings
from widgets.sidebar import CollapsibleSidebar

# Import cac tab cua du an
from tabs.home_tab    import HomeTab
from tabs.example_tab import ExampleTab


# ── Menu config — them/xoa/reorder tai day ────────────────────────────────────
# Moi entry: {"icon": "icons/layui/<name>.svg", "text": "Ten hien thi", "tab": TabClass}
# None = separator
MENU: list[dict | None] = [
    {"icon": "icons/layui/home.svg",  "text": "Trang chu", "tab": HomeTab},
    None,  # separator
    {"icon": "icons/layui/table.svg", "text": "Vi du",     "tab": ExampleTab},
    # Them muc moi:
    # {"icon": "icons/layui/user.svg",  "text": "Nhan vien", "tab": NhanVienTab},
    # {"icon": "icons/layui/set.svg",   "text": "Cai dat",   "tab": CaiDatTab},
]


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.setMinimumSize(theme.WINDOW_MIN_W, theme.WINDOW_MIN_H)

        self._build_menu()
        self._build_central()
        self._build_toolbar()   # after _build_central so self._sidebar exists

    # ── Lifecycle ─────────────────────────────────────────

    def show(self):
        super().show()
        settings.restore_window(self)

    def closeEvent(self, event):
        settings.save_window(self)
        super().closeEvent(event)

    # ── Menu ──────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        for label, shortcut, slot in [
            ("New",   "Ctrl+N", None),
            ("Open",  "Ctrl+O", None),
            ("Save",  "Ctrl+S", None),
        ]:
            act = QAction(label, self)
            act.setShortcut(shortcut)
            if slot:
                act.triggered.connect(slot)
            file_menu.addAction(act)
        file_menu.addSeparator()
        act_exit = QAction("Exit", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        edit_menu = mb.addMenu("Edit")
        for label, shortcut in [
            ("Undo",  "Ctrl+Z"),
            ("Redo",  "Ctrl+Y"),
            ("Cut",   "Ctrl+X"),
            ("Copy",  "Ctrl+C"),
            ("Paste", "Ctrl+V"),
        ]:
            act = QAction(label, self)
            act.setShortcut(shortcut)
            edit_menu.addAction(act)

        help_menu = mb.addMenu("Help")
        act_about = QAction("About", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

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

        for label in ["New", "Open", "Save", "|", "Undo", "Redo"]:
            if label == "|":
                tb.addSeparator()
            else:
                tb.addAction(QAction(label, self))

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

    # ── Slots ─────────────────────────────────────────────

    def _on_about(self):
        AboutDialog(
            self,
            app_name="My App",
            version="1.0.0",
            description="PyQt6 Desktop Application Template",
            author="Your Name",
        ).exec()
