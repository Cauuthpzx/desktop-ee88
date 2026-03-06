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


class Icon:
    """
    Central icon constants — returns QIcon on access.

    Usage:
        btn.setIcon(Icon.HOME)
        action = QAction(Icon.EDIT, "Sua", self)
    """

    # ── Sidebar / Navigation ──────────────────────────────────
    HOME = QIcon(_IconPath.HOME)
    USER = QIcon(_IconPath.USER)
    SETTINGS = QIcon(_IconPath.SETTINGS)
    MENU = QIcon(_IconPath.MENU)
    MENU_OPEN = QIcon(_IconPath.MENU_OPEN)

    # ── Actions ───────────────────────────────────────────────
    ADD = QIcon(_IconPath.ADD)
    EDIT = QIcon(_IconPath.EDIT)
    DELETE = QIcon(_IconPath.DELETE)
    SAVE = QIcon(_IconPath.SAVE)
    REFRESH = QIcon(_IconPath.REFRESH)
    SEARCH = QIcon(_IconPath.SEARCH)
    EXPORT = QIcon(_IconPath.EXPORT)
    IMPORT = QIcon(_IconPath.IMPORT)
    DOWNLOAD = QIcon(_IconPath.DOWNLOAD)
    PRINT = QIcon(_IconPath.PRINT)
    LOGOUT = QIcon(_IconPath.LOGOUT)

    # ── Input / Form ──────────────────────────────────────────
    EYE = QIcon(_IconPath.EYE)
    EYE_INVISIBLE = QIcon(_IconPath.EYE_INVISIBLE)
    KEY = QIcon(_IconPath.KEY)
    PASSWORD = QIcon(_IconPath.PASSWORD)
    EMAIL = QIcon(_IconPath.EMAIL)

    # ── Status / Feedback ─────────────────────────────────────
    OK = QIcon(_IconPath.OK)
    CLOSE = QIcon(_IconPath.CLOSE)
    NOTICE = QIcon(_IconPath.NOTICE)
    WARNING = QIcon(_IconPath.WARNING)
    TIPS = QIcon(_IconPath.TIPS)

    # ── Theme ─────────────────────────────────────────────────
    LIGHT_MODE = QIcon(_IconPath.LIGHT_MODE)
    DARK_MODE = QIcon(_IconPath.DARK_MODE)

    # ── Notification ──────────────────────────────────────────
    NOTIFICATIONS = QIcon(_IconPath.NOTIFICATIONS)

    # ── Content ───────────────────────────────────────────────
    CHART = QIcon(_IconPath.CHART)
    TABLE = QIcon(_IconPath.TABLE)
    LOG = QIcon(_IconPath.LOG)
    TEMPLATE = QIcon(_IconPath.TEMPLATE)
    WEBSITE = QIcon(_IconPath.WEBSITE)
    ABOUT = QIcon(_IconPath.ABOUT)
    FACE_SMILE = QIcon(_IconPath.FACE_SMILE)


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
