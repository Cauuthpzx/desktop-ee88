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

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QObject, QEvent
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QPolygonF, QFontMetrics, QPainterPath,
    QGuiApplication,
)

from core import theme

# ── Style constants (layui-vue inspired) ──────────────────────────────────────
_BORDER_RADIUS = 6
_PADDING_H     = 12        # horizontal padding
_PADDING_V     = 8         # vertical padding
_ARROW_SIZE    = 8          # kích thước arrow (half-diagonal of rotated square)
_SHADOW_BLUR   = 6          # margin around body for painted shadow
_SHADOW_COLOR  = QColor(0, 0, 0, 30)  # subtle shadow base color
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

        self._target: QWidget | None = None
        self._target_rect_override: QRect | None = None

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
        tip._target_rect_override = None
        tip._show()

    @classmethod
    def show_at_rect(cls, owner: QWidget, rect_global: QRect, text: str,
                     position: str = "right") -> None:
        """Hiện tooltip tại vùng rect (global coords) — dùng cho custom-painted widgets."""
        tip = cls.instance()
        tip._text = text
        tip._position = position
        tip._target = owner
        tip._target_rect_override = rect_global
        tip._show()

    @classmethod
    def hide(cls) -> None:
        tip = cls.instance()
        tip.setVisible(False)

    # Alias for backward compatibility
    hide_immediate = hide

    # ── Internal ──────────────────────────────────────────────────────────────

    def _show(self) -> None:
        if not self._target or not self._text:
            return
        self._calculate_geometry()
        self.setWindowOpacity(1.0)
        self.show()

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
        if self._target_rect_override is not None:
            target_rect = self._target_rect_override
        else:
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

        # ── Colors from palette (dark/light aware) ─────────────────────
        pal = QGuiApplication.palette()
        bg_color = pal.color(pal.ColorRole.ToolTipBase)
        text_color = pal.color(pal.ColorRole.ToolTipText)
        border_color = pal.color(pal.ColorRole.Mid)

        # ── Painted shadow (multiple expanding rects with decreasing alpha) ──
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(1, sm + 1):
            sc = QColor(_SHADOW_COLOR)
            sc.setAlpha(max(1, _SHADOW_COLOR.alpha() * (sm - i + 1) // (sm + 1)))
            p.setBrush(sc)
            p.drawRoundedRect(
                body.x() - i, body.y() - i,
                body.width() + i * 2, body.height() + i * 2,
                _BORDER_RADIUS + i, _BORDER_RADIUS + i,
            )

        # ── Draw body (rounded rect with border) ────────────────────────
        path = QPainterPath()
        path.addRoundedRect(
            body.x(), body.y(), body.width(), body.height(),
            _BORDER_RADIUS, _BORDER_RADIUS,
        )
        p.setPen(QPen(border_color, 1))
        p.setBrush(bg_color)
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
            p.setBrush(bg_color)
            p.drawPolygon(arrow)

            # Draw arrow border (outer two edges only)
            p.setPen(QPen(border_color, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(arrow[0], arrow[1])
            p.drawLine(arrow[1], arrow[2])

        # ── Draw text ────────────────────────────────────────────────────
        p.setPen(text_color)
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
