"""
widgets/notification_bell.py — Nut chuong thong bao voi badge dem so va popup panel.

Dat vao toolbar (ngoai cung ben phai). Khi co thong bao moi, badge hien so.
Nhan vao → popup panel danh sach thong bao.

Dung:
    from widgets.notification_bell import NotificationBell

    bell = NotificationBell()
    toolbar.addWidget(bell)

    # Them thong bao
    from core.icon import IconPath
    bell.add_notification("Nguoi dung moi dang ky", icon=IconPath.USER)
    bell.add_notification("Phien ban moi 2.0", icon=IconPath.REFRESH)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtGui import (
    QPainter, QColor, QIcon, QPen, QPixmap, QPalette,
    QGuiApplication,
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal, QTimer

from core import theme
from core.i18n import t
from core.theme import theme_signals


# ── Data ──────────────────────────────────────────────────────────────────────

@dataclass
class NotificationItem:
    """Du lieu 1 thong bao."""
    message: str
    icon: str = ""
    timestamp: float = field(default_factory=time.time)
    read: bool = False
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"notif_{self.timestamp}_{id(self)}"

    def time_ago(self) -> str:
        """Tra ve chuoi thoi gian tuong doi."""
        diff = int(time.time() - self.timestamp)
        if diff < 60:
            return t("notification.just_now")
        if diff < 3600:
            m = diff // 60
            return t("notification.minutes_ago", n=m)
        if diff < 86400:
            h = diff // 3600
            return t("notification.hours_ago", n=h)
        d = diff // 86400
        return t("notification.days_ago", n=d)


# ── Badge dot / count ─────────────────────────────────────────────────────────

_BADGE_COLOR = QColor(234, 67, 53)  # Google red
_BADGE_TEXT = QColor(255, 255, 255)


# ── Bell button ──────────────────────────────────────────────────────────────

class NotificationBell(QWidget):
    """Nut chuong voi badge dem so. Nhan → toggle popup."""

    notification_clicked = pyqtSignal(str)  # emit notification id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(t("notification.title"))

        self._items: list[NotificationItem] = []
        self._popup: _NotificationPopup | None = None
        from core.icon import IconPath
        self._icon_path = IconPath.NOTIFICATIONS

        theme_signals.changed.connect(self._on_theme_changed)

    # ── Public API ───────────────────────────────────────────

    def add_notification(self, message: str, icon: str = "") -> None:
        """Them 1 thong bao moi."""
        item = NotificationItem(message=message, icon=icon)
        self._items.insert(0, item)
        # Gioi han 50 thong bao
        if len(self._items) > 50:
            self._items = self._items[:50]
        self.update()
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    def unread_count(self) -> int:
        return sum(1 for n in self._items if not n.read)

    def mark_all_read(self) -> None:
        for n in self._items:
            n.read = True
        self.update()

    def clear_all(self) -> None:
        self._items.clear()
        self.update()
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    # ── Paint ────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Ve icon chuong (tinted theo palette)
        icon = theme.tinted_icon(self._icon_path, size=20)
        icon_rect = QRect(8, 8, 20, 20)
        icon.paint(p, icon_rect)

        # Badge
        count = self.unread_count()
        if count > 0:
            text = str(count) if count <= 99 else "99+"
            fm = p.fontMetrics()

            badge_font = theme.font(size=7, bold=True)
            p.setFont(badge_font)
            fm = p.fontMetrics()
            text_w = fm.horizontalAdvance(text)

            badge_w = max(text_w + 6, 16)
            badge_h = 14
            badge_x = self.width() - badge_w - 2
            badge_y = 2

            # Ve nen badge
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_BADGE_COLOR)
            p.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 7, 7)

            # Ve so
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
            self._popup.mark_all_clicked.connect(self.mark_all_read)
            self._popup.clear_all_clicked.connect(self.clear_all)

        self._popup.refresh(self._items)

        # Vi tri: ngay duoi nut chuong, can phai
        global_pos = self.mapToGlobal(QPoint(self.width(), self.height()))
        popup_w = self._popup.width()
        popup_x = global_pos.x() - popup_w
        popup_y = global_pos.y() + 4

        # Dam bao khong tran man hinh
        screen = QGuiApplication.screenAt(global_pos)
        if screen:
            sr = screen.availableGeometry()
            popup_x = max(sr.left(), min(popup_x, sr.right() - popup_w))
            popup_y = min(popup_y, sr.bottom() - self._popup.height())

        self._popup.move(popup_x, popup_y)
        self._popup.show()
        self._popup.raise_()

    def _on_item_clicked(self, notif_id: str) -> None:
        # Danh dau da doc
        for n in self._items:
            if n.id == notif_id:
                n.read = True
                break
        self.update()
        self.notification_clicked.emit(notif_id)

    def _on_theme_changed(self, _dark: bool) -> None:
        self.update()
        if self._popup and self._popup.isVisible():
            self._popup.refresh(self._items)

    def cleanup(self) -> None:
        """Goi khi dong app."""
        try:
            theme_signals.changed.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass
        if self._popup:
            self._popup.close()


# ── Popup panel ──────────────────────────────────────────────────────────────

class _NotificationPopup(QWidget):
    """Popup hien danh sach thong bao."""

    item_clicked = pyqtSignal(str)
    mark_all_clicked = pyqtSignal()
    clear_all_clicked = pyqtSignal()

    _POPUP_W = 340
    _POPUP_MAX_H = 420

    def __init__(self, parent: QWidget) -> None:
        super().__init__(
            None,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(self._POPUP_W)

        self._build_ui()

    def _build_ui(self) -> None:
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Container frame — co border va background
        self._frame = QFrame()
        self._frame.setFrameShape(QFrame.Shape.Box)
        self._frame.setFrameShadow(QFrame.Shadow.Raised)
        frame_lay = QVBoxLayout(self._frame)
        frame_lay.setContentsMargins(0, 0, 0, 0)
        frame_lay.setSpacing(0)

        # Header
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

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        frame_lay.addWidget(sep)

        # Scroll area cho danh sach
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMaximumHeight(self._POPUP_MAX_H - 100)

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

    def refresh(self, items: list[NotificationItem]) -> None:
        """Cap nhat danh sach thong bao."""
        # Xoa cac item cu
        while self._list_lay.count():
            child = self._list_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            self._scroll.hide()
            self._empty_lbl.show()
            self._btn_mark_all.setEnabled(False)
            self._btn_clear.setEnabled(False)
        else:
            self._empty_lbl.hide()
            self._scroll.show()
            self._btn_mark_all.setEnabled(True)
            self._btn_clear.setEnabled(True)

            for item in items:
                row = _NotificationRow(item)
                row.clicked_signal.connect(self.item_clicked.emit)
                self._list_lay.addWidget(row)

        # Tinh chieu cao popup
        count = len(items)
        row_h = 60
        content_h = min(count * row_h, self._POPUP_MAX_H - 100)
        if not items:
            content_h = 80
        total_h = content_h + 100  # header + footer
        self.setFixedHeight(min(total_h, self._POPUP_MAX_H))

    def _on_mark_all(self) -> None:
        self.mark_all_clicked.emit()
        self.refresh([])  # se duoc goi lai tu bell
        self.hide()

    def _on_clear_all(self) -> None:
        self.clear_all_clicked.emit()
        self.hide()


# ── Notification row ─────────────────────────────────────────────────────────

class _NotificationRow(QWidget):
    """1 dong thong bao trong popup."""

    clicked_signal = pyqtSignal(str)

    def __init__(self, item: NotificationItem) -> None:
        super().__init__()
        self._item = item
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(56)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(
            theme.SPACING_LG, theme.SPACING_SM,
            theme.SPACING_LG, theme.SPACING_SM,
        )
        lay.setSpacing(theme.SPACING_MD)

        # Cham xanh (chua doc)
        self._dot = QWidget()
        self._dot.setFixedSize(8, 8)
        if not item.read:
            self._dot.setStyleSheet(
                "background: #2a82da; border-radius: 4px;"
            )
        lay.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignTop)

        # Icon
        if item.icon:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(QIcon(item.icon).pixmap(20, 20))
            icon_lbl.setFixedSize(20, 20)
            lay.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        # Text
        text_lay = QVBoxLayout()
        text_lay.setSpacing(theme.SPACING_XS)

        msg_lbl = QLabel(item.message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setFont(theme.font(
            bold=not item.read,
            size=theme.FONT_SIZE,
        ))
        text_lay.addWidget(msg_lbl)

        time_lbl = QLabel(item.time_ago())
        time_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
        time_lbl.setEnabled(False)
        text_lay.addWidget(time_lbl)

        lay.addLayout(text_lay, 1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_signal.emit(self._item.id)
            # Dat read
            self._item.read = True
            self._dot.setStyleSheet("")
