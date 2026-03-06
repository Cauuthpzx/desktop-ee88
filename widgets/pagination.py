"""
widgets/pagination.py
Phân trang dùng chung.

Dùng:
    from widgets.pagination import Pagination
    pager = Pagination(total=100, page_size=10)
    pager.page_changed.connect(self._load_page)   # emit page_number (1-based)
    layout.addWidget(pager)

    # Cập nhật tổng số:
    pager.set_total(250)
"""
import math

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from core import theme
from core.i18n import t


class Pagination(QWidget):
    page_changed = pyqtSignal(int)   # 1-based page number

    def __init__(self, total: int = 0, page_size: int = 10):
        super().__init__()
        self._total     = total
        self._page_size = page_size
        self._current   = 1

        lay = QHBoxLayout(self)
        lay.setContentsMargins(*theme.MARGIN_ZERO)
        lay.setSpacing(theme.SPACING_SM)
        lay.addStretch()

        self._btn_first = QPushButton("«"); self._btn_first.setFixedWidth(32)
        self._btn_prev  = QPushButton("‹"); self._btn_prev.setFixedWidth(32)
        self._lbl_info  = QLabel()
        self._lbl_info.setFont(theme.font())
        self._lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._btn_next  = QPushButton("›"); self._btn_next.setFixedWidth(32)
        self._btn_last  = QPushButton("»"); self._btn_last.setFixedWidth(32)

        self._btn_first.clicked.connect(lambda: self._go(1))
        self._btn_prev.clicked.connect(lambda: self._go(self._current - 1))
        self._btn_next.clicked.connect(lambda: self._go(self._current + 1))
        self._btn_last.clicked.connect(lambda: self._go(self._total_pages()))

        for w in [self._btn_first, self._btn_prev,
                  self._lbl_info,
                  self._btn_next, self._btn_last]:
            lay.addWidget(w)

        lay.addStretch()
        self._refresh()

    def _total_pages(self) -> int:
        if self._total == 0 or self._page_size == 0:
            return 1
        return math.ceil(self._total / self._page_size)

    def _go(self, page: int):
        page = max(1, min(page, self._total_pages()))
        if page == self._current:
            return
        self._current = page
        self._refresh()
        self.page_changed.emit(self._current)

    def _refresh(self):
        tp = self._total_pages()
        self._lbl_info.setText(t("pagination.info", page=self._current, pages=tp, total=self._total))
        self._btn_first.setEnabled(self._current > 1)
        self._btn_prev.setEnabled(self._current > 1)
        self._btn_next.setEnabled(self._current < tp)
        self._btn_last.setEnabled(self._current < tp)

    def set_total(self, total: int):
        self._total   = total
        self._current = 1
        self._refresh()

    def set_page_size(self, size: int):
        self._page_size = size
        self._current   = 1
        self._refresh()

    def current_page(self) -> int:
        return self._current

    def offset(self) -> int:
        """Trả về offset (0-based) để dùng với SQL LIMIT/OFFSET."""
        return (self._current - 1) * self._page_size
