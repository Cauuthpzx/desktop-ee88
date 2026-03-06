"""
widgets/tooltip.py — Custom tooltip giống layui-vue.

Thay thế QToolTip mặc định bằng popup custom-painted với arrow, shadow, fade-in.
Cài đặt global qua install() — tự động override mọi setToolTip trong app.

Visual style (từ layui-vue):
    - Nền trắng, text #3a3a3a, border #cecece
    - Border-radius 6px, padding 8px 12px
    - Box-shadow nhẹ
    - Arrow 8px xoay 45°, border khớp tooltip
    - Fade-in 150ms

Usage:
    # Cài đặt global (trong main.py sau theme.apply):
    from widgets.tooltip import install
    install(app)

    # Mọi widget.setToolTip("text") sẽ tự dùng tooltip mới.
    # Hoặc dùng trực tiếp:
    from widgets.tooltip import Tooltip
    Tooltip.show_at(widget, "Nội dung tooltip", position="top")
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QPointF, QRect, QPropertyAnimation,
    QEasingCurve, QSize, QObject, QEvent,
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QPolygonF, QFontMetrics, QPainterPath,
    QGuiApplication, QCursor,
)

from core import theme

# ── Style constants (layui-vue inspired) ──────────────────────────────────────
_BG_COLOR      = QColor("#FFFFFF")
_TEXT_COLOR     = QColor("#3a3a3a")
_BORDER_COLOR  = QColor("#cecece")
_BORDER_RADIUS = 6
_PADDING_H     = 12        # horizontal padding
_PADDING_V     = 8         # vertical padding
_ARROW_SIZE    = 8          # kích thước arrow (half-diagonal of rotated square)
_SHADOW_BLUR   = 12
_SHADOW_COLOR  = QColor(0, 0, 0, 38)  # rgba(0,0,0,0.15)
_SHADOW_OFFSET = 2
_FADE_MS       = 150
_SHOW_DELAY    = 500        # ms chờ trước khi hiện (giống QToolTip default)
_HIDE_DELAY    = 100        # ms chờ trước khi ẩn
_MARGIN        = 4          # khoảng cách giữa arrow và target widget


class Tooltip(QWidget):
    """Custom tooltip popup — one singleton instance, reused."""

    _instance: Tooltip | None = None

    def __init__(self) -> None:
        # parent=None, window flags: no frame, stay on top, tool window
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._text = ""
        self._position = "top"     # top, bottom, left, right
        self._arrow_x = 0          # arrow center X relative to widget
        self._arrow_y = 0          # arrow center Y relative to widget

        # Fade animation
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(_FADE_MS)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(_SHADOW_BLUR)
        shadow.setColor(_SHADOW_COLOR)
        shadow.setOffset(0, _SHADOW_OFFSET)
        self.setGraphicsEffect(shadow)

        # Timers
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._do_show)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._do_hide)

        self._target: QWidget | None = None

    @classmethod
    def instance(cls) -> Tooltip:
        if cls._instance is None:
            cls._instance = Tooltip()
        return cls._instance

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def show_at(cls, target: QWidget, text: str,
                position: str = "top") -> None:
        """Hiện tooltip tại widget target."""
        tip = cls.instance()
        tip._text = text
        tip._position = position
        tip._target = target
        tip._hide_timer.stop()
        tip._show_timer.start(_SHOW_DELAY)

    @classmethod
    def hide(cls) -> None:
        tip = cls.instance()
        tip._show_timer.stop()
        if tip.isVisible():
            tip._hide_timer.start(_HIDE_DELAY)

    @classmethod
    def hide_immediate(cls) -> None:
        tip = cls.instance()
        tip._show_timer.stop()
        tip._hide_timer.stop()
        tip.setVisible(False)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _do_show(self) -> None:
        if not self._target or not self._text:
            return
        self._calculate_geometry()
        self.setWindowOpacity(0.0)
        self.show()
        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()

    def _do_hide(self) -> None:
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self._on_fade_out_done)
        self._fade_anim.start()

    def _on_fade_out_done(self) -> None:
        self._fade_anim.finished.disconnect(self._on_fade_out_done)
        self.setVisible(False)

    def _calculate_geometry(self) -> None:
        """Tính vị trí tooltip + arrow dựa trên target widget."""
        if not self._target:
            return

        fm = QFontMetrics(theme.font())
        text_w = fm.horizontalAdvance(self._text) + _PADDING_H * 2
        text_h = fm.height() + _PADDING_V * 2
        # Account for shadow margin
        shadow_m = _SHADOW_BLUR
        total_w = text_w + shadow_m * 2
        total_h = text_h + shadow_m * 2 + _ARROW_SIZE

        # Target rect in global coordinates
        target_rect = QRect(
            self._target.mapToGlobal(QPoint(0, 0)),
            self._target.size(),
        )
        tc_x = target_rect.center().x()  # target center X
        tc_y = target_rect.center().y()  # target center Y

        pos = self._position

        if pos == "top":
            x = tc_x - total_w // 2
            y = target_rect.top() - total_h - _MARGIN + shadow_m
        elif pos == "bottom":
            x = tc_x - total_w // 2
            y = target_rect.bottom() + _MARGIN - shadow_m
        elif pos == "left":
            total_w_lr = text_w + shadow_m * 2 + _ARROW_SIZE
            total_h_lr = text_h + shadow_m * 2
            x = target_rect.left() - total_w_lr - _MARGIN + shadow_m
            y = tc_y - total_h_lr // 2
            total_w = total_w_lr
            total_h = total_h_lr
        elif pos == "right":
            total_w_lr = text_w + shadow_m * 2 + _ARROW_SIZE
            total_h_lr = text_h + shadow_m * 2
            x = target_rect.right() + _MARGIN - shadow_m
            y = tc_y - total_h_lr // 2
            total_w = total_w_lr
            total_h = total_h_lr
        else:
            x = tc_x - total_w // 2
            y = target_rect.top() - total_h - _MARGIN + shadow_m

        # Screen bounds check
        screen = QGuiApplication.screenAt(target_rect.center())
        if screen:
            sr = screen.availableGeometry()
            x = max(sr.left(), min(x, sr.right() - total_w))
            y = max(sr.top(), min(y, sr.bottom() - total_h))

        self.setFixedSize(total_w, total_h)
        self.move(x, y)

        # Arrow position relative to this widget
        if pos in ("top", "bottom"):
            self._arrow_x = tc_x - x
            self._arrow_y = (shadow_m + text_h) if pos == "top" else shadow_m
        else:
            self._arrow_x = (shadow_m + text_w) if pos == "left" else shadow_m
            self._arrow_y = tc_y - y

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        sm = _SHADOW_BLUR  # shadow margin
        fm = QFontMetrics(theme.font())
        text_w = fm.horizontalAdvance(self._text) + _PADDING_H * 2
        text_h = fm.height() + _PADDING_V * 2
        pos = self._position

        # ── Body rect ────────────────────────────────────────────────────
        if pos == "top":
            body = QRect(sm, sm, text_w, text_h)
        elif pos == "bottom":
            body = QRect(sm, sm + _ARROW_SIZE, text_w, text_h)
        elif pos == "left":
            body = QRect(sm, sm, text_w, text_h)
        elif pos == "right":
            body = QRect(sm + _ARROW_SIZE, sm, text_w, text_h)
        else:
            body = QRect(sm, sm, text_w, text_h)

        # ── Draw body (rounded rect with border) ────────────────────────
        path = QPainterPath()
        path.addRoundedRect(
            body.x(), body.y(), body.width(), body.height(),
            _BORDER_RADIUS, _BORDER_RADIUS,
        )
        p.setPen(QPen(_BORDER_COLOR, 1))
        p.setBrush(_BG_COLOR)
        p.drawPath(path)

        # ── Draw arrow ───────────────────────────────────────────────────
        ax = self._arrow_x
        ay = self._arrow_y
        hs = _ARROW_SIZE // 2 + 1

        arrow = QPolygonF()
        if pos == "top":
            # Arrow pointing down (at bottom of body)
            ay = body.bottom()
            arrow.append(QPointF(ax - hs, ay))
            arrow.append(QPointF(ax, ay + hs + 1))
            arrow.append(QPointF(ax + hs, ay))
        elif pos == "bottom":
            # Arrow pointing up (at top of body)
            ay = body.top()
            arrow.append(QPointF(ax - hs, ay))
            arrow.append(QPointF(ax, ay - hs - 1))
            arrow.append(QPointF(ax + hs, ay))
        elif pos == "left":
            # Arrow pointing right (at right of body)
            ax = body.right()
            arrow.append(QPointF(ax, ay - hs))
            arrow.append(QPointF(ax + hs + 1, ay))
            arrow.append(QPointF(ax, ay + hs))
        elif pos == "right":
            # Arrow pointing left (at left of body)
            ax = body.left()
            arrow.append(QPointF(ax, ay - hs))
            arrow.append(QPointF(ax - hs - 1, ay))
            arrow.append(QPointF(ax, ay + hs))

        if not arrow.isEmpty():
            # Fill arrow (cover border at junction)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_BG_COLOR)
            p.drawPolygon(arrow)

            # Draw arrow border (only outer edges)
            p.setPen(QPen(_BORDER_COLOR, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            if pos == "top":
                p.drawLine(arrow[0], arrow[1])
                p.drawLine(arrow[1], arrow[2])
            elif pos == "bottom":
                p.drawLine(arrow[0], arrow[1])
                p.drawLine(arrow[1], arrow[2])
            elif pos == "left":
                p.drawLine(arrow[0], arrow[1])
                p.drawLine(arrow[1], arrow[2])
            elif pos == "right":
                p.drawLine(arrow[0], arrow[1])
                p.drawLine(arrow[1], arrow[2])

        # ── Draw text ────────────────────────────────────────────────────
        p.setPen(_TEXT_COLOR)
        p.setFont(theme.font())
        text_rect = body.adjusted(_PADDING_H, _PADDING_V, -_PADDING_H, -_PADDING_V)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._text)

        p.end()


# ── Global event filter — override QToolTip ──────────────────────────────────

class _TooltipFilter(QObject):
    """Event filter cài đặt trên QApplication.
    Bắt ToolTip event, thay thế bằng custom Tooltip widget."""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # type: ignore[override]
        if event.type() == QEvent.Type.ToolTip:
            widget = obj
            if isinstance(widget, QWidget) and widget.toolTip():
                Tooltip.show_at(widget, widget.toolTip(), "top")
                return True  # block QToolTip mặc định

        if event.type() == QEvent.Type.Leave:
            if isinstance(obj, QWidget) and obj.toolTip():
                Tooltip.hide()

        return False


_filter_instance: _TooltipFilter | None = None


def install(app: QApplication) -> None:
    """Cài đặt tooltip mới cho toàn bộ app.

    Gọi sau theme.apply(app) trong main.py:
        from widgets.tooltip import install
        install(app)
    """
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = _TooltipFilter()
    app.installEventFilter(_filter_instance)
