"""
widgets/search_bar.py
Thanh tìm kiếm dùng chung — QLineEdit + nút Clear.

Dùng:
    from widgets.search_bar import SearchBar
    bar = SearchBar(placeholder="Tìm theo tên...")
    bar.search_changed.connect(self._on_search)   # emit str khi gõ
    layout.addWidget(bar)
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from core import theme


class SearchBar(QWidget):
    search_changed = pyqtSignal(str)   # emit mỗi khi text thay đổi

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

    def _on_changed(self, text: str):
        self._btn_clear.setVisible(bool(text))
        self.search_changed.emit(text)

    def clear(self):
        self._edit.clear()

    def text(self) -> str:
        return self._edit.text()

    def set_focus(self):
        self._edit.setFocus()
