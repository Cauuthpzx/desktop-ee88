"""
widgets/notification_bell.py — Nút chuông thông báo với badge, popup panel, phân loại category.

Đặt vào toolbar (ngoài cùng bên phải). Khi có thông báo mới, badge hiện số.
Nhấn vào → popup panel danh sách thông báo.
Tab lọc: Tất cả | Chưa đọc | Đã đọc.
Loại thông báo (category) hiện đầu mỗi dòng.

Dùng:
    from widgets.notification_bell import NotificationBell

    bell = NotificationBell()
    toolbar.addWidget(bell)

    bell.add_notification("Phiên bản mới 2.0", category="system")
    bell.add_notification("Nạp tiền 500K", category="customer", icon=IconPath.SAVINGS)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame,
)
from PyQt6.QtGui import (
    QPainter, QColor, QIcon, QFont, QPalette,
    QGuiApplication,
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal

from core import theme
from core.i18n import t
from core.theme import theme_signals, tinted_icon


# ── Category constants ──────────────────────────────────────────────────────

CATEGORY_SYSTEM = "system"
CATEGORY_CUSTOMER = "customer"
CATEGORY_AGENT = "agent"
CATEGORY_GROUP = "group"

# Category → (i18n_key, color)
_CAT_INFO: dict[str, tuple[str, QColor]] = {
    CATEGORY_SYSTEM:   ("notification.cat_system",   QColor(66, 133, 244)),   # Blue
    CATEGORY_CUSTOMER: ("notification.cat_customer", QColor(52, 168, 83)),    # Green
    CATEGORY_AGENT:    ("notification.cat_agent",    QColor(251, 188, 4)),    # Amber
    CATEGORY_GROUP:    ("notification.cat_group",    QColor(142, 68, 173)),   # Purple
}

# Filter tabs
_FILTER_ALL = "all"
_FILTER_UNREAD = "unread"
_FILTER_READ = "read"

_FILTERS: list[tuple[str, str]] = [
    (_FILTER_ALL,    "notification.tab_all"),
    (_FILTER_UNREAD, "notification.tab_unread"),
    (_FILTER_READ,   "notification.tab_read"),
]


# ── Data ──────────────────────────────────────────────────────────────────────

@dataclass
class NotificationItem:
    """Dữ liệu 1 thông báo."""
    message: str
    category: str = CATEGORY_SYSTEM
    icon: str = ""
    timestamp: float = field(default_factory=time.time)
    read: bool = False
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"notif_{self.timestamp}_{id(self)}"

    def time_ago(self) -> str:
        """Trả về chuỗi thời gian tương đối."""
        diff = int(time.time() - self.timestamp)
        if diff < 60:
            return t("notification.just_now")
        if diff < 3600:
            return t("notification.minutes_ago", n=diff // 60)
        if diff < 86400:
            return t("notification.hours_ago", n=diff // 3600)
        return t("notification.days_ago", n=diff // 86400)

    def time_full(self) -> str:
        """Trả về chuỗi giờ:phút — ngày/tháng/năm."""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%H:%M — %d/%m/%Y")

    def category_label(self) -> str:
        """Trả về tên category đã dịch."""
        info = _CAT_INFO.get(self.category)
        return t(info[0]) if info else self.category

    def category_color(self) -> QColor:
        """Trả về màu category."""
        info = _CAT_INFO.get(self.category)
        return info[1] if info else QColor(128, 128, 128)


# ── Badge color ──────────────────────────────────────────────────────────────

_BADGE_COLOR = QColor(234, 67, 53)   # Google red
_BADGE_TEXT = QColor(255, 255, 255)


# ── Bell button ──────────────────────────────────────────────────────────────

class NotificationBell(QWidget):
    """Nút chuông với badge đếm số. Nhấn → toggle popup."""

    notification_clicked = pyqtSignal(str)  # emit notification id

    _MAX_ITEMS = 100

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(t("notification.title"))

        self._items: list[NotificationItem] = []
        self._unread_count: int = 0
        self._popup: _NotificationPopup | None = None
        from core.icon import IconPath
        self._icon_path = IconPath.NOTIFICATIONS
        self._cached_icon: QIcon | None = None

        theme_signals.changed.connect(self._on_theme_changed)

    # ── Public API ───────────────────────────────────────────

    def add_notification(
        self, message: str, *,
        category: str = CATEGORY_SYSTEM,
        icon: str = "",
    ) -> None:
        """Thêm 1 thông báo mới."""
        item = NotificationItem(message=message, category=category, icon=icon)
        self._items.insert(0, item)
        if len(self._items) > self._MAX_ITEMS:
            self._items = self._items[:self._MAX_ITEMS]
        self._update_unread_count()
        self.update()
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    def unread_count(self) -> int:
        return self._unread_count

    def _update_unread_count(self) -> None:
        self._unread_count = sum(1 for n in self._items if not n.read)

    def mark_all_read(self) -> None:
        for n in self._items:
            n.read = True
        self._unread_count = 0
        self.update()

    def clear_all(self) -> None:
        self._items.clear()
        self._unread_count = 0
        self.update()
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    # ── Paint ────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._cached_icon is None:
            self._cached_icon = tinted_icon(self._icon_path, size=20)
        icon_rect = QRect(8, 8, 20, 20)
        self._cached_icon.paint(p, icon_rect)

        count = self._unread_count
        if count > 0:
            text = str(count) if count <= 99 else "99+"
            badge_font = theme.font(size=7, bold=True)
            p.setFont(badge_font)
            text_w = p.fontMetrics().horizontalAdvance(text)

            badge_w = max(text_w + 6, 16)
            badge_h = 14
            badge_x = self.width() - badge_w - 2
            badge_y = 2

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_BADGE_COLOR)
            p.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 7, 7)

            p.setPen(_BADGE_TEXT)
            p.drawText(
                QRect(badge_x, badge_y, badge_w, badge_h),
                Qt.AlignmentFlag.AlignCenter,
                text,
            )

        p.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_popup()

    def _toggle_popup(self) -> None:
        if self._popup and self._popup.isVisible():
            self._popup.hide()
            return

        if self._popup is None:
            self._popup = _NotificationPopup(self)
            self._popup.item_clicked.connect(self._on_item_clicked)
            self._popup.mark_all_clicked.connect(self._on_mark_all)
            self._popup.clear_all_clicked.connect(self._on_clear_all)

        self._popup.refresh(self._items)

        global_pos = self.mapToGlobal(QPoint(self.width(), self.height()))
        popup_w = self._popup.width()
        popup_x = global_pos.x() - popup_w
        popup_y = global_pos.y() + 4

        screen = QGuiApplication.screenAt(global_pos)
        if screen:
            sr = screen.availableGeometry()
            popup_x = max(sr.left(), min(popup_x, sr.right() - popup_w))
            popup_y = min(popup_y, sr.bottom() - self._popup.height())

        self._popup.move(popup_x, popup_y)
        self._popup.show()
        self._popup.raise_()

    def _on_item_clicked(self, notif_id: str) -> None:
        for n in self._items:
            if n.id == notif_id:
                if not n.read:
                    n.read = True
                    self._unread_count = max(0, self._unread_count - 1)
                break
        self.update()
        self.notification_clicked.emit(notif_id)
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    def _on_mark_all(self) -> None:
        self.mark_all_read()
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    def _on_clear_all(self) -> None:
        self.clear_all()

    def _on_theme_changed(self, _dark: bool) -> None:
        self._cached_icon = None
        self.update()
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    def cleanup(self) -> None:
        """Gọi khi đóng app."""
        try:
            theme_signals.changed.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass
        if self._popup:
            self._popup.close()


# ── Popup panel ──────────────────────────────────────────────────────────────

class _NotificationPopup(QWidget):
    """Popup hiện danh sách thông báo. Tab: Tất cả | Chưa đọc | Đã đọc."""

    item_clicked = pyqtSignal(str)
    mark_all_clicked = pyqtSignal()
    clear_all_clicked = pyqtSignal()

    _POPUP_W = 380
    _POPUP_MAX_H = 480

    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            None,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self.setFixedWidth(self._POPUP_W)
        self._current_filter: str = _FILTER_ALL
        self._all_items: list[NotificationItem] = []
        self._build_ui()

    def _build_ui(self) -> None:
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        self._frame = QFrame()
        self._frame.setFrameShape(QFrame.Shape.Box)
        self._frame.setFrameShadow(QFrame.Shadow.Raised)
        frame_lay = QVBoxLayout(self._frame)
        frame_lay.setContentsMargins(0, 0, 0, 0)
        frame_lay.setSpacing(0)

        # Header: title + mark all read
        header = QWidget()
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(
            theme.SPACING_LG, theme.SPACING_MD,
            theme.SPACING_LG, theme.SPACING_MD,
        )

        self._title_lbl = QLabel(t("notification.title"))
        self._title_lbl.setFont(theme.font(bold=True))
        h_lay.addWidget(self._title_lbl)

        h_lay.addStretch()

        self._btn_mark_all = QPushButton(t("notification.mark_all_read"))
        self._btn_mark_all.setFlat(True)
        self._btn_mark_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_mark_all.setFont(theme.font(size=theme.FONT_SIZE_SM))
        self._btn_mark_all.clicked.connect(self._on_mark_all)
        h_lay.addWidget(self._btn_mark_all)

        frame_lay.addWidget(header)

        # Filter tabs: Tất cả | Chưa đọc | Đã đọc
        self._tab_row = QWidget()
        tab_lay = QHBoxLayout(self._tab_row)
        tab_lay.setContentsMargins(
            theme.SPACING_LG, 0, theme.SPACING_LG, theme.SPACING_SM,
        )
        tab_lay.setSpacing(theme.SPACING_MD)

        self._tab_buttons: dict[str, QPushButton] = {}
        for filter_id, i18n_key in _FILTERS:
            btn = QPushButton(t(i18n_key))
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(theme.font(size=theme.FONT_SIZE_SM))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, f=filter_id: self._on_filter(f))
            tab_lay.addWidget(btn)
            self._tab_buttons[filter_id] = btn

        tab_lay.addStretch()
        frame_lay.addWidget(self._tab_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        frame_lay.addWidget(sep)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMaximumHeight(self._POPUP_MAX_H - 130)

        self._list_widget = QWidget()
        self._list_lay = QVBoxLayout(self._list_widget)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(0)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._list_widget)
        frame_lay.addWidget(self._scroll, 1)

        # Empty state
        self._empty_lbl = QLabel(t("notification.empty"))
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
        self._empty_lbl.setEnabled(False)
        self._empty_lbl.setMinimumHeight(80)
        self._empty_lbl.hide()
        frame_lay.addWidget(self._empty_lbl)

        # Footer
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        frame_lay.addWidget(sep2)

        footer = QWidget()
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(
            theme.SPACING_LG, theme.SPACING_SM,
            theme.SPACING_LG, theme.SPACING_SM,
        )

        self._btn_clear = QPushButton(t("notification.clear_all"))
        self._btn_clear.setFlat(True)
        self._btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clear.setFont(theme.font(size=theme.FONT_SIZE_SM))
        self._btn_clear.clicked.connect(self._on_clear_all)
        f_lay.addStretch()
        f_lay.addWidget(self._btn_clear)

        frame_lay.addWidget(footer)
        main_lay.addWidget(self._frame)

    def _on_filter(self, filter_id: str) -> None:
        self._current_filter = filter_id
        self._update_tab_style()
        self._render_items()

    def _update_tab_style(self) -> None:
        for fid, btn in self._tab_buttons.items():
            active = fid == self._current_filter
            btn.setChecked(active)
            if active:
                btn.setStyleSheet(
                    f"color: {self.palette().color(QPalette.ColorRole.Highlight).name()};"
                    "font-weight: bold; text-decoration: underline;"
                )
            else:
                btn.setStyleSheet("")

    def refresh(self, items: list[NotificationItem]) -> None:
        """Cập nhật danh sách thông báo."""
        self._all_items = items
        self._update_tab_badges()
        self._update_tab_style()
        self._render_items()

    def _filtered_items(self) -> list[NotificationItem]:
        if self._current_filter == _FILTER_UNREAD:
            return [n for n in self._all_items if not n.read]
        if self._current_filter == _FILTER_READ:
            return [n for n in self._all_items if n.read]
        return self._all_items

    def _update_tab_badges(self) -> None:
        """Cập nhật text tab với count."""
        total = len(self._all_items)
        unread = sum(1 for n in self._all_items if not n.read)
        read = total - unread

        counts = {
            _FILTER_ALL: total,
            _FILTER_UNREAD: unread,
            _FILTER_READ: read,
        }
        for fid, i18n_key in _FILTERS:
            btn = self._tab_buttons.get(fid)
            if btn:
                c = counts.get(fid, 0)
                label = t(i18n_key)
                if c > 0:
                    label = f"{label} ({c})"
                btn.setText(label)

    def _render_items(self) -> None:
        while self._list_lay.count():
            child = self._list_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = self._filtered_items()

        if not items:
            self._scroll.hide()
            self._empty_lbl.show()
            self._btn_mark_all.setEnabled(False)
            self._btn_clear.setEnabled(False)
        else:
            self._empty_lbl.hide()
            self._scroll.show()
            has_unread = any(not n.read for n in self._all_items)
            self._btn_mark_all.setEnabled(has_unread)
            self._btn_clear.setEnabled(True)

            for item in items:
                row = _NotificationRow(item)
                row.clicked_signal.connect(self.item_clicked.emit)
                self._list_lay.addWidget(row)

        count = len(items)
        row_h = 72
        content_h = min(count * row_h, self._POPUP_MAX_H - 130)
        if not items:
            content_h = 80
        total_h = content_h + 130
        self.setFixedHeight(min(total_h, self._POPUP_MAX_H))

    def _on_mark_all(self) -> None:
        self.mark_all_clicked.emit()

    def _on_clear_all(self) -> None:
        self.clear_all_clicked.emit()
        self.hide()


# ── Notification row ─────────────────────────────────────────────────────────

class _NotificationRow(QWidget):
    """1 dòng thông báo trong popup."""

    clicked_signal = pyqtSignal(str)

    def __init__(self, item: NotificationItem) -> None:
        super().__init__()
        self._item = item
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(68)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(
            theme.SPACING_LG, theme.SPACING_SM,
            theme.SPACING_LG, theme.SPACING_SM,
        )
        lay.setSpacing(theme.SPACING_MD)

        # Chấm xanh (chưa đọc)
        self._dot = QWidget()
        self._dot.setFixedSize(8, 8)
        if not item.read:
            self._dot.setStyleSheet(
                "background: #2a82da; border-radius: 4px;"
            )
        lay.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignTop)

        # Icon (tinted theo theme)
        if item.icon:
            icon_lbl = QLabel()
            ico = tinted_icon(item.icon, size=18)
            icon_lbl.setPixmap(ico.pixmap(18, 18))
            icon_lbl.setFixedSize(18, 18)
            lay.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        # Text column
        text_lay = QVBoxLayout()
        text_lay.setSpacing(1)

        # Dòng 1: [Category] message
        cat_color = item.category_color()
        top_lay = QHBoxLayout()
        top_lay.setSpacing(theme.SPACING_SM)

        cat_lbl = QLabel(f"[ {item.category_label()} ]")
        cat_lbl.setFont(theme.font(size=8, bold=True))
        cat_lbl.setStyleSheet(f"color: {cat_color.name()};")
        top_lay.addWidget(cat_lbl)
        top_lay.addStretch()
        text_lay.addLayout(top_lay)

        # Dòng 2: message
        msg_lbl = QLabel(item.message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setFont(theme.font(
            bold=not item.read,
            size=theme.FONT_SIZE,
        ))
        text_lay.addWidget(msg_lbl)

        # Dòng 3: thời gian — chữ nhỏ nghiêng
        time_text = f"{item.time_full()}  ·  {item.time_ago()}"
        time_lbl = QLabel(time_text)
        time_font = theme.font(size=8)
        time_font.setItalic(True)
        time_lbl.setFont(time_font)
        time_lbl.setEnabled(False)
        text_lay.addWidget(time_lbl)

        lay.addLayout(text_lay, 1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_signal.emit(self._item.id)
            self._item.read = True
            self._dot.setStyleSheet("")
