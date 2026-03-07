"""
widgets/toolbar_widget.py
Toolbar nội dung (không phải QToolBar của MainWindow) — dùng trong tab.

Dùng:
    from widgets.toolbar_widget import ContentToolbar
    tb = ContentToolbar()
    tb.add_button("Thêm",   self._on_add)
    tb.add_button("Sửa",    self._on_edit,   enabled=False)
    tb.add_button("Xoá",    self._on_delete, enabled=False)
    tb.add_separator()
    tb.add_search(placeholder="Tìm kiếm...", on_change=self._on_search)
    layout.addWidget(tb)

    # Enable/disable button:
    tb.set_enabled("Sửa", True)
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from widgets.search_bar import SearchBar
from core import theme


class ContentToolbar(QWidget):
    def __init__(self):
        super().__init__()
        self._buttons: dict[str, QPushButton] = {}

        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(*theme.MARGIN_ZERO)
        self._lay.setSpacing(theme.SPACING_SM)
        self._search: SearchBar | None = None

    def add_button(self, label: str, slot=None,
                   enabled: bool = True) -> QPushButton:
        btn = QPushButton(label)
        btn.setEnabled(enabled)
        if slot:
            btn.clicked.connect(slot)
        self._buttons[label] = btn
        self._lay.addWidget(btn)
        return btn

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._lay.addWidget(line)

    def add_stretch(self):
        self._lay.addStretch()

    def add_search(self, placeholder: str = "Tìm kiếm...",
                   label: str = "",
                   on_change=None) -> SearchBar:
        self._lay.addStretch()
        bar = SearchBar(placeholder=placeholder, label=label)
        if on_change:
            bar.search_changed.connect(on_change)
        self._lay.addWidget(bar)
        self._search = bar
        return bar

    def add_icon_button(self, label: str, icon: QIcon, slot=None,
                        icon_size: int = 15) -> QPushButton:
        btn = QPushButton(icon, label)
        btn.setIconSize(QSize(icon_size, icon_size))
        if slot:
            btn.clicked.connect(slot)
        self._buttons[label] = btn
        self._lay.addWidget(btn)
        return btn

    def set_enabled(self, label: str, enabled: bool):
        if label in self._buttons:
            self._buttons[label].setEnabled(enabled)

    def set_all_enabled(self, labels: list[str], enabled: bool):
        for label in labels:
            self.set_enabled(label, enabled)

    def get_button(self, label: str) -> QPushButton | None:
        return self._buttons.get(label)
