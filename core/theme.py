"""
theme.py — Cấu hình giao diện toàn bộ ứng dụng
Import và gọi apply(app) trong main.py
"""
from PyQt6.QtWidgets import QApplication, QWidget, QLayout
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtSvg import QSvgRenderer


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
WINDOW_DEFAULT_W = 1400
WINDOW_DEFAULT_H = 900
WINDOW_MIN_W  = 960
WINDOW_MIN_H  = 640

# ── Theme state ───────────────────────────────────────────
_is_dark = False


class _ThemeSignals(QObject):
    """Global signal emitter for theme changes."""
    changed = pyqtSignal(bool)  # True = dark, False = light


theme_signals = _ThemeSignals()


def apply(app: QApplication) -> None:
    """Gọi trong main() trước khi show window."""
    from utils.settings import settings
    global _is_dark
    app.setStyle("Fusion")
    app.setFont(QFont(FONT_FAMILY, FONT_SIZE))

    _is_dark = settings.get_bool("app/dark_theme", False)
    if _is_dark:
        _apply_dark_palette(app)
    else:
        _apply_light_palette(app)


def _apply_light_palette(app: QApplication) -> None:
    """Reset về palette mặc định Fusion, rồi set Window = Base = trắng."""
    # Lấy palette gốc từ style Fusion (không phải palette hiện tại của app)
    style = app.style()
    pal = style.standardPalette()
    pal.setColor(QPalette.ColorRole.Window, pal.color(QPalette.ColorRole.Base))
    app.setPalette(pal)


def _apply_dark_palette(app: QApplication) -> None:
    """Dark palette cho Fusion style."""
    pal = QPalette()
    dark      = QColor(30, 30, 30)
    darker    = QColor(20, 20, 20)
    mid_dark  = QColor(45, 45, 45)
    text      = QColor(220, 220, 220)
    highlight = QColor(42, 130, 218)
    disabled  = QColor(127, 127, 127)
    link      = QColor(42, 130, 218)

    pal.setColor(QPalette.ColorRole.Window, dark)
    pal.setColor(QPalette.ColorRole.WindowText, text)
    pal.setColor(QPalette.ColorRole.Base, darker)
    pal.setColor(QPalette.ColorRole.AlternateBase, mid_dark)
    pal.setColor(QPalette.ColorRole.ToolTipBase, mid_dark)
    pal.setColor(QPalette.ColorRole.ToolTipText, text)
    pal.setColor(QPalette.ColorRole.Text, text)
    pal.setColor(QPalette.ColorRole.Button, mid_dark)
    pal.setColor(QPalette.ColorRole.ButtonText, text)
    pal.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    pal.setColor(QPalette.ColorRole.Link, link)
    pal.setColor(QPalette.ColorRole.Highlight, highlight)
    pal.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(140, 140, 140))

    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)

    # Mid / Dark / Light / Midlight — dùng bởi Fusion cho border/shadow
    pal.setColor(QPalette.ColorRole.Dark, QColor(15, 15, 15))
    pal.setColor(QPalette.ColorRole.Mid, QColor(60, 60, 60))
    pal.setColor(QPalette.ColorRole.Midlight, QColor(55, 55, 55))
    pal.setColor(QPalette.ColorRole.Light, QColor(70, 70, 70))
    pal.setColor(QPalette.ColorRole.Shadow, QColor(0, 0, 0))

    app.setPalette(pal)


def is_dark() -> bool:
    """Return True if current theme is dark."""
    return _is_dark


def set_theme(dark: bool) -> None:
    """Switch theme and save preference."""
    from utils.settings import settings
    global _is_dark
    if dark == _is_dark:
        return
    _is_dark = dark
    settings.set("app/dark_theme", dark)
    _tinted_icon_cache.clear()  # palette color changed
    app = QApplication.instance()
    if app:
        if dark:
            _apply_dark_palette(app)
        else:
            _apply_light_palette(app)
    theme_signals.changed.emit(dark)


def toggle_theme() -> bool:
    """Toggle between light and dark theme. Returns new is_dark state."""
    set_theme(not _is_dark)
    return _is_dark


_tinted_icon_cache: dict[tuple[str, int, int], QIcon] = {}


def tinted_icon(path: str, color: QColor | None = None, size: int = 20) -> QIcon:
    """Load SVG icon and tint it. If color is None, uses palette text color."""
    if color is None:
        app = QApplication.instance()
        color = app.palette().color(QPalette.ColorRole.WindowText) if app else QColor(0, 0, 0)

    key = (path, size, color.rgba())
    cached = _tinted_icon_cache.get(key)
    if cached is not None:
        return cached

    try:
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        QSvgRenderer(path).render(p)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(px.rect(), color)
        p.end()
        icon = QIcon(px)
    except Exception:  # noqa: BLE001 — fallback to untinted icon
        icon = QIcon(path)

    _tinted_icon_cache[key] = icon
    return icon


_font_cache: dict[tuple[int, bool, bool], QFont] = {}


def font(size: int = FONT_SIZE, bold: bool = False, italic: bool = False) -> QFont:
    """Tạo QFont chuẩn theo theme. Cached — returns same QFont for same params."""
    key = (size, bold, italic)
    cached = _font_cache.get(key)
    if cached is not None:
        return cached
    f = QFont(FONT_FAMILY, size)
    f.setBold(bold)
    f.setItalic(italic)
    _font_cache[key] = f
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
