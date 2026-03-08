"""
widgets/notify.py
Lightweight toast notification overlay — dùng chung cho cả app.

Hiển thị notify card (nền đen 70%, icon animated, text) rồi tự ẩn.
Loại: success (tick xanh), error (X đỏ), warn (! cam), info (i xanh).

Dùng:
    from widgets.notify import NotifyOverlay

    # Gắn vào bất kỳ widget nào:
    self._notify = NotifyOverlay(parent_widget)

    # Hiện thông báo:
    self._notify.show_notify("success", "Đã lưu thành công!")
    self._notify.show_notify("error", "Không thể kết nối.")
    self._notify.show_notify("warn", "Dữ liệu đã thay đổi.")
    self._notify.show_notify("info", "Đã cập nhật.")
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtCore import pyqtProperty  # type: ignore[attr-defined]
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QPainterPath, QPaintEvent, QResizeEvent,
)
from core import theme


# ── Colors & durations ───────────────────────────────────

COLOR_SUCCESS = QColor(76, 175, 80)    # Material Green 500
COLOR_ERROR   = QColor(244, 67, 54)    # Material Red 500
COLOR_WARN    = QColor(255, 152, 0)    # Material Orange 500
COLOR_INFO    = QColor(33, 150, 243)   # Material Blue 500

COLORS: dict[str, QColor] = {
    "success": COLOR_SUCCESS,
    "error":   COLOR_ERROR,
    "warn":    COLOR_WARN,
    "info":    COLOR_INFO,
}

DURATIONS: dict[str, int] = {
    "success": 800,
    "error":   2000,
    "warn":    1500,
    "info":    1200,
}


# ── Animated icon ────────────────────────────────────────

class NotifyIcon(QWidget):
    """Animated icon for success/error/warn/info notifications."""

    def __init__(self, size: int = 28, parent: QWidget | None = None):
        super().__init__(parent)
        self._size = size
        self._progress = 0.0
        self._icon_type = "success"
        self._color = COLOR_SUCCESS
        self.setFixedSize(size, size)

    def set_type(self, icon_type: str) -> None:
        self._icon_type = icon_type
        self._color = COLORS.get(icon_type, COLOR_SUCCESS)
        self._progress = 0.0
        self.update()

    def _get_progress(self) -> float:
        return self._progress

    def _set_progress(self, val: float) -> None:
        self._progress = val
        self.update()

    progress = pyqtProperty(float, _get_progress, _set_progress)

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        if self._progress <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = self._size
        pen = QPen(self._color, 2.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        # Circle
        m = 2
        p.drawEllipse(m, m, s - m * 2, s - m * 2)

        prog = self._progress
        if self._icon_type == "success":
            self._draw_tick(p, s, prog)
        elif self._icon_type == "error":
            self._draw_cross(p, s, prog)
        elif self._icon_type == "warn":
            self._draw_exclamation(p, s, prog)
        elif self._icon_type == "info":
            self._draw_info(p, s, prog)

        p.end()

    def _draw_tick(self, p: QPainter, s: int, prog: float) -> None:
        x1, y1 = s * 0.28, s * 0.52
        x2, y2 = s * 0.43, s * 0.67
        x3, y3 = s * 0.72, s * 0.35
        if prog <= 0.5:
            frac = prog / 0.5
            path = QPainterPath()
            path.moveTo(x1, y1)
            path.lineTo(x1 + (x2 - x1) * frac, y1 + (y2 - y1) * frac)
            p.drawPath(path)
        else:
            frac = (prog - 0.5) / 0.5
            path = QPainterPath()
            path.moveTo(x1, y1)
            path.lineTo(x2, y2)
            path.lineTo(x2 + (x3 - x2) * frac, y2 + (y3 - y2) * frac)
            p.drawPath(path)

    def _draw_cross(self, p: QPainter, s: int, prog: float) -> None:
        cx, cy = s * 0.5, s * 0.5
        arm = s * 0.18
        if prog <= 0.5:
            frac = prog / 0.5
            path = QPainterPath()
            path.moveTo(cx - arm, cy - arm)
            path.lineTo(cx - arm + 2 * arm * frac, cy - arm + 2 * arm * frac)
            p.drawPath(path)
        else:
            frac = (prog - 0.5) / 0.5
            p.drawLine(int(cx - arm), int(cy - arm),
                       int(cx + arm), int(cy + arm))
            path = QPainterPath()
            path.moveTo(cx + arm, cy - arm)
            path.lineTo(cx + arm - 2 * arm * frac, cy - arm + 2 * arm * frac)
            p.drawPath(path)

    def _draw_exclamation(self, p: QPainter, s: int, prog: float) -> None:
        cx = s * 0.5
        if prog <= 0.6:
            frac = prog / 0.6
            top_y = s * 0.25
            bot_y = s * 0.58
            path = QPainterPath()
            path.moveTo(cx, top_y)
            path.lineTo(cx, top_y + (bot_y - top_y) * frac)
            p.drawPath(path)
        else:
            p.drawLine(int(cx), int(s * 0.25), int(cx), int(s * 0.58))
            frac = (prog - 0.6) / 0.4
            if frac > 0.5:
                dot_y = s * 0.72
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(self._color)
                p.drawEllipse(int(cx - 2.5), int(dot_y - 2.5), 5, 5)

    def _draw_info(self, p: QPainter, s: int, prog: float) -> None:
        cx = s * 0.5
        if prog <= 0.4:
            frac = prog / 0.4
            if frac > 0.5:
                dot_y = s * 0.28
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(self._color)
                p.drawEllipse(int(cx - 2.5), int(dot_y - 2.5), 5, 5)
        else:
            dot_y = s * 0.28
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._color)
            p.drawEllipse(int(cx - 2.5), int(dot_y - 2.5), 5, 5)

            pen = QPen(self._color, 2.5, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            frac = (prog - 0.4) / 0.6
            top_y = s * 0.42
            bot_y = s * 0.75
            path = QPainterPath()
            path.moveTo(cx, top_y)
            path.lineTo(cx, top_y + (bot_y - top_y) * frac)
            p.drawPath(path)


# ── Notify card ──────────────────────────────────────────

class NotifyCard(QWidget):
    """Rounded dark card showing icon + label for any notification type."""

    _BG = QColor(0, 0, 0, 178)  # 70% opacity
    _RADIUS = 10

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 14, 24, 14)
        lay.setSpacing(theme.SPACING_SM)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = NotifyIcon(28, parent=self)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(theme.font())
        self._label.setStyleSheet("color: white;")
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(280)
        lay.addWidget(self._label)

    @property
    def icon(self) -> NotifyIcon:
        return self._icon

    @property
    def label(self) -> QLabel:
        return self._label

    def set_type(self, notify_type: str) -> None:
        self._icon.set_type(notify_type)

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._BG)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), self._RADIUS, self._RADIUS)
        p.end()


# ── Lightweight notify overlay ───────────────────────────

class NotifyOverlay(QWidget):
    """Overlay chỉ chứa notify card — dùng cho toast notification nhẹ.

    Không có loading dots. Gắn vào bất kỳ widget nào.
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = NotifyCard(parent=self)
        self._card.hide()
        lay.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignCenter)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._final_hide)
        self._icon_anim: QPropertyAnimation | None = None

    def notify(self, notify_type: str, text: str = "") -> None:
        """Show notification with animated icon.

        Args:
            notify_type: "success" | "error" | "warn" | "info"
            text: Message to display.
        """
        self._hide_timer.stop()
        self._stop_anim()

        self._card.set_type(notify_type)
        self._card.label.setText(text)
        self._card.icon._progress = 0.0
        self._card.show()

        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        self.show()
        self.raise_()

        self._icon_anim = QPropertyAnimation(
            self._card.icon, b"progress", self)
        self._icon_anim.setDuration(350)
        self._icon_anim.setStartValue(0.0)
        self._icon_anim.setEndValue(1.0)
        self._icon_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._icon_anim.start()

        duration = DURATIONS.get(notify_type, 1000)
        self._hide_timer.start(duration)

    def _stop_anim(self) -> None:
        if self._icon_anim:
            self._icon_anim.stop()
            self._icon_anim = None

    def _final_hide(self) -> None:
        self.hide()
        self._card.hide()
        self._card.icon._progress = 0.0

    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        super().resizeEvent(event)
