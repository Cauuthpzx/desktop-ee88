"""
widgets/empty_state.py
Hiển thị khi không có dữ liệu — với illustration SVG đẹp.

Dùng:
    from widgets.empty_state import EmptyState
    empty = EmptyState("Không có dữ liệu", "Thêm bản ghi mới để bắt đầu")
    layout.addWidget(empty)

    # Ẩn/hiện tuỳ theo có data không:
    empty.setVisible(len(data) == 0)
    table.setVisible(len(data) > 0)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap, QPainter, QPalette
from PyQt6.QtSvg import QSvgRenderer
from core import theme
from core.i18n import t
from core.theme import theme_signals

# Inline SVG — empty box illustration (simple, clean, works in both themes)
_EMPTY_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 160" fill="none">
  <!-- Box body -->
  <path d="M40 65 L100 95 L160 65 L160 115 L100 145 L40 115Z"
        fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>
  <!-- Box lid left -->
  <path d="M40 65 L100 35 L100 95 L40 65Z"
        fill="{lid_l}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>
  <!-- Box lid right -->
  <path d="M160 65 L100 35 L100 95 L160 65Z"
        fill="{lid_r}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>
  <!-- Magnifying glass -->
  <circle cx="130" cy="38" r="16" fill="none" stroke="{accent}" stroke-width="2.5"/>
  <line x1="142" y1="49" x2="154" y2="61" stroke="{accent}" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Question mark inside glass -->
  <text x="130" y="44" text-anchor="middle" font-size="16" font-weight="bold"
        fill="{accent}" font-family="sans-serif">?</text>
</svg>"""


def _render_empty_pixmap(dark: bool) -> QPixmap:
    """Render the empty state SVG with colors matching the current theme."""
    if dark:
        colors = {
            "fill": "#2a2a3a",
            "lid_l": "#353548",
            "lid_r": "#2f2f42",
            "stroke": "#555570",
            "accent": "#7a7a9a",
        }
    else:
        colors = {
            "fill": "#f0f0f5",
            "lid_l": "#e0e0ea",
            "lid_r": "#d8d8e5",
            "stroke": "#b0b0c0",
            "accent": "#9090a8",
        }

    svg_data = _EMPTY_SVG.format(**colors).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(svg_data))
    pixmap = QPixmap(160, 128)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


class EmptyState(QWidget):
    def __init__(self, title: str = "",
                 description: str = ""):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(theme.SPACING_MD)

        # SVG illustration
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._img_lbl)

        self._title_lbl = QLabel(title or t("empty.title"))
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setFont(theme.font(size=theme.FONT_SIZE_LG, bold=True))
        lay.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(description or t("empty.add_hint"))
        self._desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desc_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
        self._desc_lbl.setWordWrap(True)
        # Muted text color
        pal = self._desc_lbl.palette()
        c = pal.color(QPalette.ColorRole.WindowText)
        c.setAlpha(140)
        pal.setColor(QPalette.ColorRole.WindowText, c)
        self._desc_lbl.setPalette(pal)
        lay.addWidget(self._desc_lbl)

        self._refresh_pixmap()
        theme_signals.changed.connect(self._on_theme_changed)
        # AUDIT-FIX: disconnect on destroy to prevent memory leak
        self.destroyed.connect(self._cleanup_signals)

    def _refresh_pixmap(self) -> None:
        dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        self._img_lbl.setPixmap(_render_empty_pixmap(dark))

    def _cleanup_signals(self) -> None:
        """AUDIT-FIX: disconnect theme signal on destroy."""
        try:
            theme_signals.changed.disconnect(self._on_theme_changed)
        except (TypeError, RuntimeError):
            pass

    def _on_theme_changed(self, _dark: bool) -> None:
        self._refresh_pixmap()
