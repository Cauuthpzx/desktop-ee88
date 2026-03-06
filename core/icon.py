"""
core/icon.py — Central icon registry for the entire app.

Moi icon dung trong app deu khai bao tai day de dong bo, de thay doi.
Khong hardcode path "icons/..." trong code nua — import tu day.

Usage:
    from core.icon import Icon, GalleryIcon

    btn.setIcon(Icon.EDIT)
    btn.setIcon(Icon.HOME)
    action = QAction(Icon.DELETE, "Xoa", self)

    # Gallery icons (black/white variant theo theme)
    btn.setIcon(GalleryIcon.GRID.icon())
    btn.setIcon(GalleryIcon.GRID.icon(dark=True))

    # Tinted icon (auto-match palette text color)
    from core.icon import tinted
    btn.setIcon(tinted(Icon.LIGHT_MODE))
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from PyQt6.QtGui import QIcon

_GALLERY_DIR = Path("icons/gallery")


# ── Main icon registry ─────────────────────────────────────────
# Moi constant la QIcon — dung truc tiep: btn.setIcon(Icon.HOME)

class _IconPath:
    """Namespace for all icon paths used across the app."""

    # ── App icons (taskbar, titlebar, tray) ────────────────────
    APP_TASKBAR = "icons/app/icon-taskbar"
    APP_TITLEBAR = "icons/app/icon-titlebar"
    APP_TRAY = "icons/app/icon-tray"

    # ── Sidebar / Navigation ──────────────────────────────────
    HOME = "icons/layui/home.svg"
    USER = "icons/layui/user.svg"
    SETTINGS = "icons/layui/set.svg"
    MENU = "icons/material/menu.svg"
    MENU_OPEN = "icons/material/menu_open.svg"

    # ── Actions ───────────────────────────────────────────────
    ADD = "icons/layui/add-circle.svg"
    EDIT = "icons/layui/edit.svg"
    DELETE = "icons/layui/delete.svg"
    SAVE = "icons/layui/ok-circle.svg"
    REFRESH = "icons/layui/refresh.svg"
    SEARCH = "icons/layui/search.svg"
    EXPORT = "icons/layui/export.svg"
    IMPORT = "icons/layui/upload.svg"
    DOWNLOAD = "icons/layui/download-circle.svg"
    PRINT = "icons/layui/print.svg"
    LOGOUT = "icons/layui/logout.svg"

    # ── Input / Form ──────────────────────────────────────────
    EYE = "icons/layui/eye.svg"
    EYE_INVISIBLE = "icons/layui/eye-invisible.svg"
    KEY = "icons/layui/key.svg"
    PASSWORD = "icons/layui/password.svg"
    EMAIL = "icons/layui/email.svg"

    # ── Status / Feedback ─────────────────────────────────────
    OK = "icons/layui/ok-circle.svg"
    CLOSE = "icons/layui/close-fill.svg"
    NOTICE = "icons/layui/notice.svg"
    WARNING = "icons/layui/warning.svg"
    TIPS = "icons/layui/tips.svg"

    # ── Theme ─────────────────────────────────────────────────
    LIGHT_MODE = "icons/material/light_mode.svg"
    DARK_MODE = "icons/material/dark_mode.svg"

    # ── Notification ──────────────────────────────────────────
    NOTIFICATIONS = "icons/material/notifications.svg"

    # ── Content ───────────────────────────────────────────────
    CHART = "icons/layui/chart.svg"
    TABLE = "icons/layui/table.svg"
    LOG = "icons/layui/log.svg"
    TEMPLATE = "icons/layui/template.svg"
    WEBSITE = "icons/layui/website.svg"
    ABOUT = "icons/layui/about.svg"
    FACE_SMILE = "icons/layui/face-smile.svg"

    # ── Material extended ────────────────────────────────────
    GROUPS = "icons/material/groups.svg"
    CASINO = "icons/material/casino.svg"
    RECEIPT = "icons/material/receipt_long.svg"
    STORE = "icons/material/store.svg"
    WALLET = "icons/material/account_balance_wallet.svg"
    SAVINGS = "icons/material/savings.svg"
    MONEY_OFF = "icons/material/money_off.svg"
    LIST_ALT = "icons/material/list_alt.svg"


class _IconMeta(type):
    """Metaclass: lazy-load QIcon on first attribute access."""

    _cache: dict[str, QIcon] = {}

    def __getattr__(cls, name: str) -> QIcon:
        if name.startswith("_"):
            raise AttributeError(name)
        cached = cls._cache.get(name)
        if cached is not None:
            return cached
        path = getattr(_IconPath, name, None)
        if path is None:
            raise AttributeError(f"Icon.{name} not found in IconPath")
        icon = QIcon(path)
        cls._cache[name] = icon
        return icon


class Icon(metaclass=_IconMeta):
    """
    Central icon constants — lazy-loaded QIcon on first access.

    Usage:
        btn.setIcon(Icon.HOME)
        action = QAction(Icon.EDIT, "Sua", self)
    """
    pass


# ── Gallery icons (black/white variant) ────────────────────────

class GalleryIcon(Enum):
    """Gallery custom icons — moi icon co variant _black.svg va _white.svg."""

    GRID = "Grid"
    MENU = "Menu"
    TEXT = "Text"
    PRICE = "Price"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"

    def path(self, dark: bool = False) -> str:
        """Tra ve path toi SVG file. dark=True -> dung variant trang (cho dark theme)."""
        color = "white" if dark else "black"
        return str(_GALLERY_DIR / f"{self.value}_{color}.svg")

    def icon(self, dark: bool = False) -> QIcon:
        """Tra ve QIcon tu SVG file."""
        return QIcon(self.path(dark))


# ── Helper: tinted icon (re-export from theme) ────────────────

def tinted(path_or_icon: str, **kwargs) -> QIcon:
    """
    Load SVG icon and tint to match current palette text color.
    Wrapper around theme.tinted_icon() for convenience.

    Usage:
        from core.icon import Icon, tinted
        btn.setIcon(tinted(IconPath.LIGHT_MODE))
    """
    from core.theme import tinted_icon
    return tinted_icon(path_or_icon, **kwargs)


# ── Path access for special cases ─────────────────────────────
# Dung khi can path string (vd: sidebar pixmap, expand_card pixmap)
IconPath = _IconPath
