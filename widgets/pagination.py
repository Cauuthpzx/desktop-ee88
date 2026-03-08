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

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSpinBox
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from core import theme
from core.i18n import t
from core.icon import Icon, IconPath
from core.theme import tinted_icon, theme_signals

_ICON_SIZE = QSize(18, 18)
_BTN_SIZE = 28


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

        # Total rows label (left side)
        self._lbl_total = QLabel()
        self._lbl_total.setFont(theme.font())
        lay.addWidget(self._lbl_total)

        lay.addStretch()

        self._btn_first = self._icon_btn(IconPath.FIRST_PAGE)
        self._btn_prev  = self._icon_btn(IconPath.CHEVRON_LEFT)
        self._lbl_info  = QLabel()
        self._lbl_info.setFont(theme.font())
        self._lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._btn_next  = self._icon_btn(IconPath.CHEVRON_RIGHT)
        self._btn_last  = self._icon_btn(IconPath.LAST_PAGE)

        self._btn_first.clicked.connect(lambda: self._go(1))
        self._btn_prev.clicked.connect(lambda: self._go(self._current - 1))
        self._btn_next.clicked.connect(lambda: self._go(self._current + 1))
        self._btn_last.clicked.connect(lambda: self._go(self._total_pages()))

        # Go-to page input
        self._go_label = QLabel(t("pagination.go_to"))
        self._go_label.setFont(theme.font())
        self._go_spin = QSpinBox()
        self._go_spin.setRange(1, 1)
        self._go_spin.setFixedWidth(60)
        self._go_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._go_btn = QPushButton(t("pagination.go"))
        self._go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._go_btn.clicked.connect(self._on_go)

        for w in [self._btn_first, self._btn_prev,
                  self._lbl_info,
                  self._btn_next, self._btn_last,
                  self._go_label, self._go_spin, self._go_btn]:
            lay.addWidget(w)

        lay.addStretch()
        self._refresh()

        # Refresh icons on theme change
        theme_signals.changed.connect(self._on_theme_changed)
        # AUDIT-FIX: disconnect on destroy to prevent memory leak
        self.destroyed.connect(self._cleanup_signals)

    @staticmethod
    def _icon_btn(icon_path: str) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(tinted_icon(icon_path, size=18))
        btn.setIconSize(_ICON_SIZE)
        btn.setFixedSize(_BTN_SIZE, _BTN_SIZE)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

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

    def _on_go(self):
        self._go(self._go_spin.value())

    def _refresh(self):
        tp = self._total_pages()
        self._lbl_total.setText(t("pagination.total_rows", total=self._total))
        self._lbl_info.setText(t("pagination.info", page=self._current, pages=tp, total=self._total))
        self._btn_first.setEnabled(self._current > 1)
        self._btn_prev.setEnabled(self._current > 1)
        self._btn_next.setEnabled(self._current < tp)
        self._btn_last.setEnabled(self._current < tp)
        self._go_spin.setRange(1, tp)
        self._go_spin.setValue(self._current)

    def set_total(self, total: int, reset_page: bool = True):
        self._total = total
        if reset_page:
            self._current = 1
        else:
            # Clamp current page to valid range
            self._current = max(1, min(self._current, self._total_pages()))
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

    def _cleanup_signals(self) -> None:
        """AUDIT-FIX: disconnect theme signal on destroy."""
        try:
            theme_signals.changed.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass

    def _on_theme_changed(self, _dark: bool) -> None:
        self._btn_first.setIcon(tinted_icon(IconPath.FIRST_PAGE, size=18))
        self._btn_prev.setIcon(tinted_icon(IconPath.CHEVRON_LEFT, size=18))
        self._btn_next.setIcon(tinted_icon(IconPath.CHEVRON_RIGHT, size=18))
        self._btn_last.setIcon(tinted_icon(IconPath.LAST_PAGE, size=18))
