"""
widgets/loading.py
Loading indicators: LoadingBar (inline), LoadingOverlay (overlay with dots + notify).

Dùng:
    from widgets.loading import LoadingBar, LoadingOverlay

    # 1. Loading bar đơn giản (nhúng vào layout):
    bar = LoadingBar()
    layout.addWidget(bar)
    bar.start()
    bar.stop()

    # 2. Overlay với loading dots + tick xanh khi hoàn tất:
    overlay = LoadingOverlay(parent_widget)
    overlay.start("Đang tải...")
    overlay.stop()  # hiện tick xanh → tự ẩn sau 800ms

    # 3. Toast notification (thay dialog):
    overlay.notify("success", "Xuất file thành công!")
    overlay.notify("error", "Không thể kết nối.")
    overlay.notify("warn", "Dữ liệu đã thay đổi.")
    overlay.notify("info", "Đã cập nhật phiên bản mới.")
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QProgressBar, QLabel,
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtCore import pyqtProperty  # type: ignore[attr-defined]
from PyQt6.QtGui import (
    QPainter, QColor, QPalette, QPen, QPainterPath, QPaintEvent, QResizeEvent,
)
from core import theme
from core.i18n import t

# Icon colors per notification type
_COLOR_SUCCESS = QColor(76, 175, 80)    # Material Green 500
_COLOR_ERROR = QColor(244, 67, 54)      # Material Red 500
_COLOR_WARN = QColor(255, 152, 0)       # Material Orange 500
_COLOR_INFO = QColor(33, 150, 243)      # Material Blue 500

_COLORS = {
    "success": _COLOR_SUCCESS,
    "error": _COLOR_ERROR,
    "warn": _COLOR_WARN,
    "info": _COLOR_INFO,
}

# Auto-hide duration per type (ms)
_DURATIONS = {
    "success": 800,
    "error": 2000,
    "warn": 1500,
    "info": 1200,
}


class LoadingBar(QWidget):
    """Progress bar indeterminate + label text."""
    def __init__(self, text: str = ""):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(*theme.MARGIN_ZERO)
        lay.setSpacing(theme.SPACING_SM)

        self._label = QLabel(text or t("loading.processing"))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(theme.font())

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)   # indeterminate
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)

        lay.addWidget(self._label)
        lay.addWidget(self._bar)
        self.hide()

    def start(self, text: str | None = None) -> None:
        if text:
            self._label.setText(text)
        self.show()

    def stop(self) -> None:
        self.hide()

    def set_text(self, text: str) -> None:
        self._label.setText(text)


# ── Dot animation ────────────────────────────────────────

class _Dot(QWidget):
    """Single animated dot."""

    def __init__(self, color: QColor, size: int = 6,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._color = color
        self._size = size
        self._opacity = 0.2
        self.setFixedSize(size, size)

    def _get_opacity(self) -> float:
        return self._opacity

    def _set_opacity(self, val: float) -> None:
        self._opacity = val
        self.update()

    opacity = pyqtProperty(float, _get_opacity, _set_opacity)

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, self._size, self._size)
        p.end()


class _LoadingDots(QWidget):
    """5 dots pulse animation (Win10 style)."""

    def __init__(self, color: QColor | None = None, dot_size: int = 6,
                 gap: int = 6, parent: QWidget | None = None):
        super().__init__(parent)
        if color is None:
            color = self.palette().color(QPalette.ColorRole.Highlight)
        self._dots: list[_Dot] = []

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(gap)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for _ in range(5):
            dot = _Dot(color, dot_size, self)
            self._dots.append(dot)
            lay.addWidget(dot)

        self.setFixedSize(dot_size * 5 + gap * 4, dot_size)
        self._timers: list[QTimer] = []
        self._anims: list[QPropertyAnimation] = []

    def start(self) -> None:
        self._stop_all()
        for i, dot in enumerate(self._dots):
            dot._opacity = 0.2
            dot.update()

            anim = QPropertyAnimation(dot, b"opacity", self)
            anim.setDuration(600)
            anim.setStartValue(0.2)
            anim.setKeyValueAt(0.5, 1.0)
            anim.setEndValue(0.2)
            anim.setEasingCurve(QEasingCurve.Type.InOutSine)
            anim.setLoopCount(-1)
            self._anims.append(anim)

            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(i * 200)
            timer.timeout.connect(anim.start)
            timer.start()
            self._timers.append(timer)

    def stop(self) -> None:
        self._stop_all()
        for dot in self._dots:
            dot._opacity = 0.2
            dot.update()

    def _stop_all(self) -> None:
        for timer in self._timers:
            timer.stop()
        self._timers.clear()
        for anim in self._anims:
            anim.stop()
        self._anims.clear()


# ── Notification icons ───────────────────────────────────

class _NotifyIcon(QWidget):
    """Animated icon for success/error/warn/info notifications."""

    def __init__(self, size: int = 28, parent: QWidget | None = None):
        super().__init__(parent)
        self._size = size
        self._progress = 0.0
        self._icon_type = "success"
        self._color = _COLOR_SUCCESS
        self.setFixedSize(size, size)

    def set_type(self, icon_type: str) -> None:
        self._icon_type = icon_type
        self._color = _COLORS.get(icon_type, _COLOR_SUCCESS)
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

class _NotifyCard(QWidget):
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

        self._icon = _NotifyIcon(28, parent=self)
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(theme.font())
        self._label.setStyleSheet("color: white;")
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(280)
        lay.addWidget(self._label)

    @property
    def icon(self) -> _NotifyIcon:
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


# ── Overlay ──────────────────────────────────────────────

class LoadingOverlay(QWidget):
    """Overlay with loading dots + notify card (success/error/warn/info)."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Loading dots (no dark bg)
        self._dots = _LoadingDots(parent=self)
        lay.addWidget(self._dots, alignment=Qt.AlignmentFlag.AlignCenter)

        # Loading label
        self._loading_label = QLabel(t("loading.processing"))
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setFont(theme.font())
        lay.addWidget(self._loading_label)

        # Notify card (dark bg, hidden initially)
        self._notify_card = _NotifyCard(parent=self)
        self._notify_card.hide()
        lay.addWidget(self._notify_card, alignment=Qt.AlignmentFlag.AlignCenter)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._final_hide)
        self._icon_anim: QPropertyAnimation | None = None
        self._loading = False

    def start(self, text: str = "") -> None:
        self._hide_timer.stop()
        self._stop_anim()
        self._loading = True
        self._notify_card.hide()
        self._notify_card.icon._progress = 0.0
        self._dots.show()
        self._loading_label.show()
        self._loading_label.setText(text or t("loading.processing"))
        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        self._dots.start()
        self.show()
        self.raise_()

    def stop(self) -> None:
        """Stop loading and show success tick (backward compatible).

        Safe to call multiple times — only the first call after start()
        triggers the notification. Subsequent calls are no-ops.
        """
        if not self._loading:
            return
        self._loading = False
        self.notify("success", t("loading.complete"))

    def notify(self, notify_type: str, text: str = "") -> None:
        """Show notification overlay with animated icon.

        Args:
            notify_type: "success" | "error" | "warn" | "info"
            text: Message to display.
        """
        self._loading = False
        self._hide_timer.stop()
        self._dots.stop()
        self._dots.hide()
        self._loading_label.hide()
        self._stop_anim()

        self._notify_card.set_type(notify_type)
        self._notify_card.label.setText(text)
        self._notify_card.icon._progress = 0.0
        self._notify_card.show()

        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        self.show()
        self.raise_()

        self._icon_anim = QPropertyAnimation(
            self._notify_card.icon, b"progress", self)
        self._icon_anim.setDuration(350)
        self._icon_anim.setStartValue(0.0)
        self._icon_anim.setEndValue(1.0)
        self._icon_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._icon_anim.start()

        duration = _DURATIONS.get(notify_type, 1000)
        self._hide_timer.start(duration)

    def _stop_anim(self) -> None:
        if self._icon_anim:
            self._icon_anim.stop()
            self._icon_anim = None

    def _final_hide(self) -> None:
        self.hide()
        self._notify_card.hide()
        self._notify_card.icon._progress = 0.0

    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        super().resizeEvent(event)
