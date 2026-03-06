"""
core/icon.py — Enum-based icon registry for plain PyQt6.

Ported from gallery project (qfluentwidgets FluentIconBase).
Hỗ trợ black/white variant theo theme — hiện tại app dùng light theme nên mặc định black.

Usage:
    from core.icon import GalleryIcon
    btn.setIcon(GalleryIcon.GRID.icon())
    action = QAction(GalleryIcon.MENU.icon(), "Menu", self)
"""
from __future__ import annotations
from enum import Enum
from pathlib import Path

from PyQt6.QtGui import QIcon


_GALLERY_DIR = Path("icons/gallery")


class GalleryIcon(Enum):
    """Gallery custom icons — mỗi icon có variant _black.svg và _white.svg."""

    GRID = "Grid"
    MENU = "Menu"
    TEXT = "Text"
    PRICE = "Price"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"

    def path(self, dark: bool = False) -> str:
        """Trả về path tới SVG file. dark=True → dùng variant trắng (cho dark theme)."""
        color = "white" if dark else "black"
        return str(_GALLERY_DIR / f"{self.value}_{color}.svg")

    def icon(self, dark: bool = False) -> QIcon:
        """Trả về QIcon từ SVG file."""
        return QIcon(self.path(dark))
