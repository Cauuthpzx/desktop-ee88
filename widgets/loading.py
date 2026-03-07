"""
widgets/loading.py
Loading indicators: LoadingBar (inline), LoadingOverlay (overlay with dots).

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

_TICK_COLOR = QColor(76, 175, 80)  # Material Green 500


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


# ── Tick icon ─────────────────────────────────────────────

class _TickIcon(QWidget):
    """Animated green checkmark."""

    def __init__(self, size: int = 24, parent: QWidget | None = None):
        super().__init__(parent)
        self._size = size
        self._progress = 0.0  # 0..1 for draw animation
        self.setFixedSize(size, size)

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
        pen = QPen(_TICK_COLOR, 2.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        # Draw circle
        margin = 2
        p.drawEllipse(margin, margin, s - margin * 2, s - margin * 2)

        # Draw checkmark (proportional to progress)
        x1, y1 = s * 0.28, s * 0.52
        x2, y2 = s * 0.43, s * 0.67
        x3, y3 = s * 0.72, s * 0.35

        prog = self._progress
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

        p.end()


# ── Overlay ───────────────────────────────────────────────

class LoadingOverlay(QWidget):
    """Overlay nền đen 70% với loading dots + tick xanh khi hoàn tất."""

    _BG_COLOR = QColor(0, 0, 0, 178)  # 70% opacity

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(theme.SPACING_MD)
        c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Dots (white on dark bg)
        self._dots = _LoadingDots(
            color=QColor(255, 255, 255), parent=container)
        c_lay.addWidget(self._dots, alignment=Qt.AlignmentFlag.AlignCenter)

        # Tick (hidden initially)
        self._tick = _TickIcon(28, parent=container)
        self._tick.hide()
        c_lay.addWidget(self._tick, alignment=Qt.AlignmentFlag.AlignCenter)

        # Label (white text)
        self._label = QLabel(t("loading.processing"))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(theme.font())
        self._label.setStyleSheet("color: white;")
        c_lay.addWidget(self._label)

        lay.addWidget(container)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._final_hide)
        self._tick_anim: QPropertyAnimation | None = None

    def start(self, text: str = "") -> None:
        self._hide_timer.stop()
        if self._tick_anim:
            self._tick_anim.stop()
            self._tick_anim = None
        self._tick.hide()
        self._tick._progress = 0.0
        self._dots.show()
        self._label.setText(text or t("loading.processing"))
        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        self._dots.start()
        self.show()
        self.raise_()

    def stop(self) -> None:
        self._dots.stop()
        self._dots.hide()

        # Show tick with animation
        self._tick.show()
        self._label.setText(t("loading.complete"))

        self._tick_anim = QPropertyAnimation(self._tick, b"progress", self)
        self._tick_anim.setDuration(350)
        self._tick_anim.setStartValue(0.0)
        self._tick_anim.setEndValue(1.0)
        self._tick_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._tick_anim.start()

        # Auto-hide after 800ms
        self._hide_timer.start(800)

    def _final_hide(self) -> None:
        self.hide()
        self._tick.hide()
        self._tick._progress = 0.0
        self._dots.show()

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.fillRect(self.rect(), self._BG_COLOR)
        p.end()

    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        super().resizeEvent(event)
