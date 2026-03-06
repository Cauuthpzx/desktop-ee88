"""
theme.py — Cấu hình giao diện toàn bộ ứng dụng
Import và gọi apply(app) trong main.py
"""
from PyQt6.QtWidgets import QApplication, QWidget, QLayout
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt


# ── Typography ────────────────────────────────────────────
FONT_FAMILY   = "Segoe UI"
FONT_SIZE     = 10        # pt
FONT_SIZE_SM  = 9
FONT_SIZE_LG  = 12
FONT_SIZE_XL  = 16

# ── Spacing ───────────────────────────────────────────────
SPACING_XS    = 2
SPACING_SM    = 4
SPACING_MD    = 8
SPACING_LG    = 16
SPACING_XL    = 24

MARGIN_DEFAULT   = (10, 10, 10, 10)   # left, top, right, bottom
MARGIN_ZERO      = (0, 0, 0, 0)
MARGIN_DIALOG    = (16, 16, 16, 16)

# ── Sizing ────────────────────────────────────────────────
INPUT_HEIGHT     = 26     # px — chiều cao chuẩn input
BUTTON_HEIGHT    = 28
TOOLBAR_HEIGHT   = 36
SIDEBAR_WIDTH           = 200
SIDEBAR_COLLAPSED_WIDTH = 48
SIDEBAR_ANIM_MS         = 150   # animation duration in milliseconds
HEADER_HEIGHT           = 48

# ── Window defaults ───────────────────────────────────────
WINDOW_MIN_W  = 960
WINDOW_MIN_H  = 640


def apply(app: QApplication) -> None:
    """Gọi trong main() trước khi show window."""
    app.setStyle("Fusion")
    app.setFont(QFont(FONT_FAMILY, FONT_SIZE))

    # Nền trắng toàn app — Window = Base = trắng
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window, pal.color(QPalette.ColorRole.Base))
    app.setPalette(pal)


def font(size: int = FONT_SIZE, bold: bool = False, italic: bool = False) -> QFont:
    """Tạo QFont chuẩn theo theme."""
    f = QFont(FONT_FAMILY, size)
    f.setBold(bold)
    f.setItalic(italic)
    return f


def set_layout_default(layout: QLayout, spacing: int = SPACING_MD) -> None:
    """Áp dụng margin + spacing chuẩn cho bất kỳ layout nào."""
    l, t, r, b = MARGIN_DEFAULT
    layout.setContentsMargins(l, t, r, b)
    layout.setSpacing(spacing)


def set_layout_tight(layout: QLayout) -> None:
    """Layout không có margin, spacing nhỏ — dùng trong group/card."""
    layout.setContentsMargins(*MARGIN_ZERO)
    layout.setSpacing(SPACING_SM)
