"""
widgets/expand_card.py — Expandable card widget.

Compact header row (icon + title + description + arrow) that expands
to reveal content on click. Inspired by PyQt-Fluent-Widgets ExpandSettingCard.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy, QGraphicsOpacityEffect,
)
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QFont, QPalette
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtProperty,
    QParallelAnimationGroup, QSize,
)
from core import theme


class _ExpandArrow(QWidget):
    """Small arrow indicator that rotates 0 -> 180 degrees."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle: float = 0.0
        self.setFixedSize(20, 20)

    def get_angle(self) -> float:
        return self._angle

    def set_angle(self, v: float) -> None:
        self._angle = v
        self.update()

    angle = pyqtProperty(float, get_angle, set_angle)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self.palette().color(QPalette.ColorRole.WindowText)
        color.setAlpha(160)
        pen = QPen(color, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.translate(10, 10)
        p.rotate(self._angle)
        # Draw a simple chevron (V shape pointing down at angle=0)
        p.drawLine(-4, -2, 0, 2)
        p.drawLine(0, 2, 4, -2)
        p.end()


class ExpandCard(QFrame):
    """
    A card with a clickable header that expands/collapses content below it.

    Usage:
        card = ExpandCard(icon="icons/layui/user.svg", title="Profile")
        card.add_widget(some_widget)
        card.set_description("username: admin")
    """

    ANIM_DURATION = 200

    def __init__(
        self,
        icon: str = "",
        title: str = "",
        description: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._expanded = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        # Main layout
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Header ───────────────────────────────────────────
        self._header = QWidget()
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setMinimumHeight(theme.HEADER_HEIGHT)

        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(theme.SPACING_LG, theme.SPACING_MD,
                                 theme.SPACING_LG, theme.SPACING_MD)
        h_lay.setSpacing(theme.SPACING_MD)

        # Icon
        self._icon_lbl = QLabel()
        if icon:
            self._icon_lbl.setPixmap(QIcon(icon).pixmap(20, 20))
        self._icon_lbl.setFixedSize(20, 20)
        h_lay.addWidget(self._icon_lbl)

        # Title
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(theme.font(bold=True))
        h_lay.addWidget(self._title_lbl)

        h_lay.addStretch()

        # Description (right-side summary text)
        self._desc_lbl = QLabel(description)
        self._desc_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
        desc_color = self.palette().color(QPalette.ColorRole.WindowText)
        desc_color.setAlpha(140)
        self._desc_lbl.setStyleSheet(f"color: rgba({desc_color.red()},{desc_color.green()},{desc_color.blue()},0.55);")
        h_lay.addWidget(self._desc_lbl)

        # Arrow
        self._arrow = _ExpandArrow()
        h_lay.addWidget(self._arrow)

        main_lay.addWidget(self._header)

        # ── Content area ─────────────────────────────────────
        self._content = QWidget()
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(
            theme.SPACING_LG, theme.SPACING_SM,
            theme.SPACING_LG, theme.SPACING_LG,
        )
        self._content_lay.setSpacing(theme.SPACING_MD)
        self._content.setMaximumHeight(0)

        main_lay.addWidget(self._content)

        # ── Animations ───────────────────────────────────────
        self._anim_group = QParallelAnimationGroup(self)

        self._anim_height = QPropertyAnimation(self._content, b"maximumHeight")
        self._anim_height.setDuration(self.ANIM_DURATION)
        self._anim_height.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim_group.addAnimation(self._anim_height)

        self._anim_arrow = QPropertyAnimation(self._arrow, b"angle")
        self._anim_arrow.setDuration(self.ANIM_DURATION)
        self._anim_arrow.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._anim_group.addAnimation(self._anim_arrow)

        # Click handler on header
        self._header.mousePressEvent = lambda _e: self.toggle()

    # ── Public API ───────────────────────────────────────────

    def add_widget(self, widget: QWidget) -> None:
        """Add a widget to the expandable content area."""
        self._content_lay.addWidget(widget)

    def add_layout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        """Add a layout to the expandable content area."""
        self._content_lay.addLayout(layout)

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text)

    def set_description(self, text: str) -> None:
        self._desc_lbl.setText(text)

    def set_icon(self, icon_path: str) -> None:
        self._icon_lbl.setPixmap(QIcon(icon_path).pixmap(20, 20))

    def is_expanded(self) -> bool:
        return self._expanded

    def toggle(self) -> None:
        """Toggle expand/collapse."""
        if self._expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self) -> None:
        if self._expanded:
            return
        self._expanded = True

        # Calculate content height
        content_height = self._content_lay.sizeHint().height()
        content_height += self._content_lay.contentsMargins().top()
        content_height += self._content_lay.contentsMargins().bottom()
        # Add a bit of extra space
        content_height = max(content_height, 50)

        self._anim_group.stop()
        self._anim_height.setStartValue(0)
        self._anim_height.setEndValue(content_height)
        self._anim_arrow.setStartValue(0.0)
        self._anim_arrow.setEndValue(180.0)
        self._anim_group.start()

    def collapse(self) -> None:
        if not self._expanded:
            return
        self._expanded = False

        self._anim_group.stop()
        self._anim_height.setStartValue(self._content.height())
        self._anim_height.setEndValue(0)
        self._anim_arrow.setStartValue(180.0)
        self._anim_arrow.setEndValue(0.0)
        self._anim_group.start()

    @property
    def content_layout(self) -> QVBoxLayout:
        """Direct access to the content layout for complex builds."""
        return self._content_lay
