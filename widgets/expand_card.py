"""
widgets/expand_card.py — Expandable card widget.

Compact header row (icon + title + description + arrow) that expands
to reveal content on click. Inspired by PyQt-Fluent-Widgets ExpandSettingCard.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
)
from PyQt6.QtGui import QPainter, QPen, QPalette
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtProperty,
    QParallelAnimationGroup,
)
from core import theme
from core.theme import theme_signals, tinted_icon


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

    def _get_card_height(self) -> int:
        return self._card_height

    def _set_card_height(self, h: int) -> None:
        self._card_height = h
        self.setFixedHeight(h)

    cardHeight = pyqtProperty(int, _get_card_height, _set_card_height)

    def __init__(
        self,
        icon: str = "",
        title: str = "",
        description: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._expanded = False
        self._icon_path = icon
        self._header_height = theme.HEADER_HEIGHT

        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Start collapsed — fixed to header height
        self._card_height = self._header_height
        self.setFixedHeight(self._header_height)

        # Main layout
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Header ───────────────────────────────────────────
        self._header = QWidget()
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setFixedHeight(self._header_height)

        h_lay = QHBoxLayout(self._header)
        h_lay.setContentsMargins(theme.SPACING_LG, theme.SPACING_MD,
                                 theme.SPACING_LG, theme.SPACING_MD)
        h_lay.setSpacing(theme.SPACING_MD)

        # Icon
        self._icon_lbl = QLabel()
        if icon:
            self._icon_lbl.setPixmap(tinted_icon(icon).pixmap(20, 20))
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
        self._desc_lbl.setEnabled(False)  # uses disabled palette text = subtle
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
        self._content.hide()

        main_lay.addWidget(self._content)

        # ── Animations ───────────────────────────────────────
        self._anim_group = QParallelAnimationGroup(self)

        self._anim_height = QPropertyAnimation(self, b"cardHeight")
        self._anim_height.setDuration(self.ANIM_DURATION)
        self._anim_height.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_group.addAnimation(self._anim_height)

        self._anim_arrow = QPropertyAnimation(self._arrow, b"angle")
        self._anim_arrow.setDuration(self.ANIM_DURATION)
        self._anim_arrow.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_group.addAnimation(self._anim_arrow)

        # Click handler on header
        self._header.mousePressEvent = lambda _e: self.toggle()

        # Re-tint icon on theme change
        theme_signals.changed.connect(self._on_theme_changed)

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
        self._icon_path = icon_path
        self._icon_lbl.setPixmap(tinted_icon(icon_path).pixmap(20, 20))

    def _on_theme_changed(self, _dark: bool) -> None:
        if self._icon_path:
            self._icon_lbl.setPixmap(tinted_icon(self._icon_path).pixmap(20, 20))

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

        # Show content so layout can calculate size
        self._content.show()
        self._content.adjustSize()
        content_h = self._content.sizeHint().height()
        target = self._header_height + max(content_h, 50)

        self._anim_group.stop()
        self._anim_height.setStartValue(self._header_height)
        self._anim_height.setEndValue(target)
        self._anim_arrow.setStartValue(0.0)
        self._anim_arrow.setEndValue(180.0)
        self._anim_group.start()

    def collapse(self) -> None:
        if not self._expanded:
            return
        self._expanded = False

        self._anim_group.stop()
        self._anim_height.setStartValue(self.height())
        self._anim_height.setEndValue(self._header_height)
        self._anim_arrow.setStartValue(180.0)
        self._anim_arrow.setEndValue(0.0)
        self._anim_group.start()
        self._anim_group.finished.connect(self._hide_content_once)

    def _hide_content_once(self) -> None:
        """Hide content after collapse animation finishes."""
        if not self._expanded:
            self._content.hide()
        self._anim_group.finished.disconnect(self._hide_content_once)

    @property
    def content_layout(self) -> QVBoxLayout:
        """Direct access to the content layout for complex builds."""
        return self._content_lay
