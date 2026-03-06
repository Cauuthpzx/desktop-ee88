"""
widgets/search_bar.py
Thanh tìm kiếm dùng chung — QLineEdit + nút Clear + debounce 300ms.

Dùng:
    from widgets.search_bar import SearchBar
    bar = SearchBar(placeholder="Tìm theo tên...")
    bar.search_changed.connect(self._on_search)   # emit str sau 300ms debounce
    layout.addWidget(bar)
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from core import theme

_DEBOUNCE_MS = 300


class SearchBar(QWidget):
    search_changed = pyqtSignal(str)   # emit sau debounce khi text thay đổi

    def __init__(self, placeholder: str = "Tìm kiếm...",
                 label: str = "", min_width: int = 220):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(*theme.MARGIN_ZERO)
        lay.setSpacing(theme.SPACING_SM)

        if label:
            lbl = QLabel(label)
            lbl.setFont(theme.font())
            lay.addWidget(lbl)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.setMinimumWidth(min_width)
        self._edit.textChanged.connect(self._on_changed)
        lay.addWidget(self._edit)

        self._btn_clear = QPushButton("✕")
        self._btn_clear.setFixedWidth(28)
        self._btn_clear.setFlat(True)
        self._btn_clear.setVisible(False)
        self._btn_clear.clicked.connect(self.clear)
        lay.addWidget(self._btn_clear)

        # Debounce timer
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._emit_search)

    def _on_changed(self, text: str) -> None:
        self._btn_clear.setVisible(bool(text))
        self._debounce.start()

    def _emit_search(self) -> None:
        self.search_changed.emit(self._edit.text())

    def clear(self) -> None:
        self._edit.clear()

    def text(self) -> str:
        return self._edit.text()

    def set_focus(self) -> None:
        self._edit.setFocus()
