"""
widgets/tooltip.py — Custom tooltip.

Nền đen trong suốt 50%, chữ trắng, border-radius, arrow — mọi chế độ.
Hiện ngay khi hover (không delay).

Cài đặt global qua install() — tự động override mọi setToolTip trong app.

Usage:
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

# ── Style constants ───────────────────────────────────────────────────────────
_BORDER_RADIUS = 6
_PADDING_H     = 10        # horizontal padding
_PADDING_V     = 6         # vertical padding
_ARROW_SIZE    = 6          # arrow triangle height
_MARGIN        = 4          # gap between arrow tip and target widget

# Fixed colors — same in both light and dark mode
_BG_COLOR      = QColor(0, 0, 0, 204)   # black 80% transparent
_TEXT_COLOR     = QColor(255, 255, 255)  # white
_BORDER_COLOR  = QColor(255, 255, 255, 30)  # subtle white border


class Tooltip(QWidget):
    """Custom tooltip popup — one singleton instance, reused."""

    _instance: Tooltip | None = None

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._text = ""
        self._position = "top"
        self._arrow_x = 0
        self._arrow_y = 0

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

    hide_immediate = hide

    # ── Internal ──────────────────────────────────────────────────────────────

    def _show(self) -> None:
        if not self._target or not self._text:
            return
        self._calculate_geometry()
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

    def _calculate_geometry(self) -> None:
        if not self._target:
            return

        fm = QFontMetrics(theme.font())
        text_w = fm.horizontalAdvance(self._text) + _PADDING_H * 2
        text_h = fm.height() + _PADDING_V * 2

        # For top/bottom: arrow adds height. For left/right: arrow adds width.
        if self._target_rect_override is not None:
            target_rect = self._target_rect_override
        else:
            target_rect = QRect(
                self._target.mapToGlobal(QPoint(0, 0)),
                self._target.size(),
            )
        tc_x = target_rect.center().x()
        tc_y = target_rect.center().y()

        pos = self._position

        if pos == "top":
            total_w = text_w
            total_h = text_h + _ARROW_SIZE
            x = tc_x - total_w // 2
            y = target_rect.top() - total_h - _MARGIN
        elif pos == "bottom":
            total_w = text_w
            total_h = text_h + _ARROW_SIZE
            x = tc_x - total_w // 2
            y = target_rect.bottom() + _MARGIN
        elif pos == "left":
            total_w = text_w + _ARROW_SIZE
            total_h = text_h
            x = target_rect.left() - total_w - _MARGIN
            y = tc_y - total_h // 2
        elif pos == "right":
            total_w = text_w + _ARROW_SIZE
            total_h = text_h
            x = target_rect.right() + _MARGIN
            y = tc_y - total_h // 2
        else:
            total_w = text_w
            total_h = text_h + _ARROW_SIZE
            x = tc_x - total_w // 2
            y = target_rect.top() - total_h - _MARGIN

        # Screen bounds
        screen = QGuiApplication.screenAt(target_rect.center())
        if screen:
            sr = screen.availableGeometry()
            x = max(sr.left(), min(x, sr.right() - total_w))
            y = max(sr.top(), min(y, sr.bottom() - total_h))

        self.setFixedSize(total_w, total_h)
        self.move(x, y)

        # Arrow center relative to this widget
        if pos in ("top", "bottom"):
            self._arrow_x = tc_x - x
            self._arrow_y = text_h if pos == "top" else 0
        else:
            self._arrow_x = text_w if pos == "left" else 0
            self._arrow_y = tc_y - y

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        fm = QFontMetrics(theme.font())
        text_w = fm.horizontalAdvance(self._text) + _PADDING_H * 2
        text_h = fm.height() + _PADDING_V * 2
        pos = self._position

        # ── Body rect ────────────────────────────────────────────────────
        if pos == "top":
            body = QRect(0, 0, text_w, text_h)
        elif pos == "bottom":
            body = QRect(0, _ARROW_SIZE, text_w, text_h)
        elif pos == "left":
            body = QRect(0, 0, text_w, text_h)
        elif pos == "right":
            body = QRect(_ARROW_SIZE, 0, text_w, text_h)
        else:
            body = QRect(0, 0, text_w, text_h)

        # ── Draw body ────────────────────────────────────────────────────
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
            ay = body.bottom()
            arrow.append(QPointF(ax - hs, ay))
            arrow.append(QPointF(ax, ay + _ARROW_SIZE))
            arrow.append(QPointF(ax + hs, ay))
        elif pos == "bottom":
            ay = body.top()
            arrow.append(QPointF(ax - hs, ay))
            arrow.append(QPointF(ax, ay - _ARROW_SIZE))
            arrow.append(QPointF(ax + hs, ay))
        elif pos == "left":
            ax = body.right()
            arrow.append(QPointF(ax, ay - hs))
            arrow.append(QPointF(ax + _ARROW_SIZE, ay))
            arrow.append(QPointF(ax, ay + hs))
        elif pos == "right":
            ax = body.left()
            arrow.append(QPointF(ax, ay - hs))
            arrow.append(QPointF(ax - _ARROW_SIZE, ay))
            arrow.append(QPointF(ax, ay + hs))

        if not arrow.isEmpty():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_BG_COLOR)
            p.drawPolygon(arrow)

        # ── Draw text ────────────────────────────────────────────────────
        p.setPen(_TEXT_COLOR)
        p.setFont(theme.font())
        text_rect = body.adjusted(_PADDING_H, _PADDING_V, -_PADDING_H, -_PADDING_V)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._text)

        p.end()


# ── Global event filter — override QToolTip ──────────────────────────────────

class _TooltipFilter(QObject):
    """Event filter: intercept both ToolTip and HoverMove events.

    QEvent.Type.ToolTip fires with OS delay (~700ms) — too slow.
    We also listen to HoverMove/HoverEnter for instant tooltips on
    widgets that have toolTip set.
    """

    def __init__(self) -> None:
        super().__init__()
        self._hover_widget: QWidget | None = None

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # type: ignore[override]
        etype = event.type()

        # Block the default QToolTip entirely
        if etype == QEvent.Type.ToolTip:
            if isinstance(obj, QWidget) and obj.toolTip():
                # Already shown via HoverEnter/Move — just block default
                return True

        # Show instantly on hover enter/move
        if etype in (QEvent.Type.HoverEnter, QEvent.Type.HoverMove):
            if isinstance(obj, QWidget) and obj.toolTip():
                if self._hover_widget is not obj:
                    self._hover_widget = obj
                    Tooltip.show_at(obj, obj.toolTip(), "top")
                return False

        # Hide on hover leave
        if etype == QEvent.Type.HoverLeave:
            if isinstance(obj, QWidget) and obj is self._hover_widget:
                self._hover_widget = None
                Tooltip.hide()
            return False

        # Also hide on Leave (for widgets without hover tracking)
        if etype == QEvent.Type.Leave:
            if isinstance(obj, QWidget) and obj.toolTip():
                if obj is self._hover_widget:
                    self._hover_widget = None
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
