"""
widgets/date_range_picker.py
Date range picker — 1 nút hiển thị "2025-03-01 ~ 2025-03-07",
click mở popup với 1 bảng lịch duy nhất. Click lần 1 = chọn ngày bắt đầu,
click lần 2 = chọn ngày kết thúc, highlight range.
Dropdown chọn nhanh: Hôm nay, Hôm qua, Tuần này, Tháng này, Tháng trước.

Dùng:
    from widgets.date_range_picker import DateRangePicker

    picker = DateRangePicker()
    picker.range_changed.connect(lambda f, t: print(f, t))
    picker.text()  # "2025-03-01|2025-03-07"
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QCalendarWidget, QLabel, QFrame, QComboBox,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QPoint
from PyQt6.QtGui import QTextCharFormat, QColor
from core import theme
from core.icon import IconPath
from core.theme import tinted_icon, theme_signals


class _RangeCalendar(QCalendarWidget):
    """Calendar that highlights a date range."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGridVisible(True)
        self.setMaximumDate(QDate.currentDate())
        self._range_from: QDate | None = None
        self._range_to: QDate | None = None

    def set_range(self, d_from: QDate | None, d_to: QDate | None) -> None:
        self._range_from = d_from
        self._range_to = d_to
        self._apply_highlight()

    def _apply_highlight(self) -> None:
        # Clear all formats first
        clear_fmt = QTextCharFormat()
        self.setDateTextFormat(QDate(), clear_fmt)

        if not self._range_from:
            return

        # Highlight start/end date
        end_fmt = QTextCharFormat()
        end_fmt.setBackground(QColor(42, 130, 218))
        end_fmt.setForeground(QColor(255, 255, 255))
        self.setDateTextFormat(self._range_from, end_fmt)

        if not self._range_to or self._range_to == self._range_from:
            return

        self.setDateTextFormat(self._range_to, end_fmt)

        # Highlight range between
        range_fmt = QTextCharFormat()
        range_fmt.setBackground(QColor(42, 130, 218, 80))
        d = self._range_from.addDays(1)
        while d < self._range_to:
            self.setDateTextFormat(d, range_fmt)
            d = d.addDays(1)


# Preset keys — value = callable(today) → (d_from, d_to)
def _presets():
    """Return list of (i18n_key, calc_fn) for quick date presets."""
    return [
        ("search.preset_today", lambda td: (td, td)),
        ("search.preset_yesterday", lambda td: (td.addDays(-1), td.addDays(-1))),
        ("search.preset_this_week", lambda td: (
            td.addDays(-(td.dayOfWeek() - 1)), td,
        )),
        ("search.preset_this_month", lambda td: (
            QDate(td.year(), td.month(), 1), td,
        )),
        ("search.preset_last_month", lambda td: (
            QDate(td.year(), td.month(), 1).addMonths(-1),
            QDate(td.year(), td.month(), 1).addDays(-1),
        )),
    ]


class _RangePopup(QFrame):
    """Popup with 1 calendar — click twice to select range."""

    confirmed = pyqtSignal(QDate, QDate)

    def __init__(self, parent=None, d_from: QDate = None, d_to: QDate = None):
        super().__init__(parent, Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        self._d_from = d_from
        self._d_to = d_to
        self._click_count = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(theme.SPACING_MD, theme.SPACING_MD,
                                theme.SPACING_MD, theme.SPACING_MD)
        root.setSpacing(theme.SPACING_SM)

        # Status label showing current selection
        self._lbl_status = QLabel()
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._lbl_status)

        # Single calendar
        self._cal = _RangeCalendar()
        if d_from:
            self._cal.setSelectedDate(d_from)
            self._cal.set_range(d_from, d_to)
        self._cal.clicked.connect(self._on_date_clicked)
        root.addWidget(self._cal)

        # Bottom row: preset dropdown + confirm button
        btns = QHBoxLayout()

        # Quick preset dropdown
        from core.i18n import t
        self._preset_combo = QComboBox()
        self._preset_combo.addItem(t("search.preset_label"), None)
        self._preset_fns: list = []
        for key, fn in _presets():
            self._preset_combo.addItem(t(key), len(self._preset_fns))
            self._preset_fns.append(fn)
        self._preset_combo.currentIndexChanged.connect(self._on_preset)
        btns.addWidget(self._preset_combo)

        btns.addStretch()

        self._btn_ok = QPushButton(t("search.confirm"))
        self._btn_ok.clicked.connect(self._on_confirm)
        btns.addWidget(self._btn_ok)

        root.addLayout(btns)
        self._update_status()

    def _on_preset(self, index: int) -> None:
        idx = self._preset_combo.currentData()
        if idx is None:
            return
        today = QDate.currentDate()
        d_from, d_to = self._preset_fns[idx](today)
        self._set_range(d_from, d_to)

    def _on_date_clicked(self, date: QDate) -> None:
        # User clicked manually — reset preset dropdown
        self._preset_combo.blockSignals(True)
        self._preset_combo.setCurrentIndex(0)
        self._preset_combo.blockSignals(False)

        if self._click_count == 0:
            self._d_from = date
            self._d_to = None
            self._click_count = 1
            self._cal.set_range(date, None)
        else:
            if date < self._d_from:
                self._d_to = self._d_from
                self._d_from = date
            else:
                self._d_to = date
            self._click_count = 0
            self._cal.set_range(self._d_from, self._d_to)
        self._update_status()

    def _update_status(self) -> None:
        from core.i18n import t
        if self._d_from and self._d_to:
            f = self._d_from.toString("yyyy-MM-dd")
            to = self._d_to.toString("yyyy-MM-dd")
            self._lbl_status.setText(f"{f}  ~  {to}")
        elif self._d_from:
            f = self._d_from.toString("yyyy-MM-dd")
            self._lbl_status.setText(f"{f}  ~  {t('search.pick_end')}")
        else:
            self._lbl_status.setText(t("search.pick_start"))

    def _set_range(self, d_from: QDate, d_to: QDate) -> None:
        self._d_from = d_from
        self._d_to = d_to
        self._click_count = 0
        self._cal.set_range(d_from, d_to)
        self._cal.setSelectedDate(d_from)
        self._update_status()

    def _on_confirm(self) -> None:
        if self._d_from and self._d_to:
            self.confirmed.emit(self._d_from, self._d_to)
            self.close()
        elif self._d_from:
            self.confirmed.emit(self._d_from, self._d_from)
            self.close()


class DateRangePicker(QWidget):
    """Single-input date range picker with popup calendar.

    Args:
        optional: If True, starts with no date selected (shows "Tất cả").
                  text() returns "" when no date is selected.
    """

    range_changed = pyqtSignal(QDate, QDate)

    def __init__(self, d_from: QDate = None, d_to: QDate = None,
                 optional: bool = False, parent=None):
        super().__init__(parent)
        self._optional = optional

        if optional and d_from is None:
            self._d_from: QDate | None = None
            self._d_to: QDate | None = None
        else:
            self._d_from = d_from or QDate.currentDate().addDays(-7)
            self._d_to = d_to or QDate.currentDate()

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._btn = QPushButton()
        self._btn.setIcon(tinted_icon(IconPath.DATE_RANGE))
        self._btn.clicked.connect(self._show_popup)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_text()
        lay.addWidget(self._btn)

        theme_signals.changed.connect(self._on_theme_changed)
        # AUDIT-FIX: disconnect on destroy to prevent memory leak
        self.destroyed.connect(self._cleanup_signals)

    def _cleanup_signals(self) -> None:
        """AUDIT-FIX: disconnect theme signal on destroy."""
        try:
            theme_signals.changed.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass

    def _update_text(self) -> None:
        if self._d_from and self._d_to:
            f = self._d_from.toString("yyyy-MM-dd")
            t = self._d_to.toString("yyyy-MM-dd")
            self._btn.setText(f"  {f}  ~  {t}  ")
        else:
            from core.i18n import t
            self._btn.setText(f"  {t('search.all')}  ")

    def _show_popup(self) -> None:
        popup = _RangePopup(self, self._d_from, self._d_to)
        popup.confirmed.connect(self._on_confirmed)

        pos = self._btn.mapToGlobal(QPoint(0, self._btn.height()))
        popup.move(pos)
        popup.show()

    def _on_confirmed(self, d_from: QDate, d_to: QDate) -> None:
        self._d_from = d_from
        self._d_to = d_to
        self._update_text()
        self.range_changed.emit(d_from, d_to)

    # ── Public API ──────────────────────────────────────────

    def date_from(self) -> QDate | None:
        return self._d_from

    def date_to(self) -> QDate | None:
        return self._d_to

    def text(self) -> str:
        """Return "yyyy-MM-dd|yyyy-MM-dd" for upstream param, or "" if unset."""
        if self._d_from and self._d_to:
            return (f"{self._d_from.toString('yyyy-MM-dd')}"
                    f"|{self._d_to.toString('yyyy-MM-dd')}")
        return ""

    def set_range(self, d_from: QDate, d_to: QDate) -> None:
        self._d_from = d_from
        self._d_to = d_to
        self._update_text()

    def reset(self) -> None:
        """Reset to initial state (optional → clear, otherwise → default range)."""
        if self._optional:
            self._d_from = None
            self._d_to = None
        else:
            self._d_from = QDate.currentDate()
            self._d_to = QDate.currentDate()
        self._update_text()

    def _on_theme_changed(self, _dark: bool) -> None:
        self._btn.setIcon(tinted_icon(IconPath.DATE_RANGE))
