"""
widgets/sidebar.py — Collapsible sidebar navigation.

Custom-painted sidebar: ZERO child widgets. Mọi thứ vẽ bằng paintEvent.
Icon position tính bằng toán — không phụ thuộc layout engine — nên KHÔNG BAO GIỜ
dịch chuyển dù animation đang chạy.

Usage:
    sidebar = CollapsibleSidebar()
    sidebar.add_button("home", "Trang chu", "icons/layui/home.svg")
    sidebar.add_button("nhanvien", "Nhan vien", "icons/layui/user.svg")
    sidebar.button_clicked.connect(lambda key: ...)
    # hoặc dùng page_changed với QStackedWidget:
    sidebar.add_item("icons/layui/home.svg", "Trang chu", home_widget)
    sidebar.page_changed.connect(stack.setCurrentWidget)
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QParallelAnimationGroup,
    QEasingCurve, pyqtSignal, QPoint, QRect, QRectF, QSize,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QCursor, QMouseEvent
from core import theme

import logging
_logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────
_W_EXPANDED  = theme.SIDEBAR_WIDTH            # 200
_W_COLLAPSED = theme.SIDEBAR_COLLAPSED_WIDTH   # 48
_ICON_SIZE   = 20
_NAV_ICON_SIZE = 18                            # icon nav items (nhỏ hơn toggle 2px)
_BTN_H       = 36                              # chiều cao mỗi item
_ANIM_MS     = theme.SIDEBAR_ANIM_MS           # 150
_NAV_PAD     = (_W_COLLAPSED - _BTN_H) // 2    # padding trái = (48-36)/2 = 6
_ACCENT_W    = 3                               # độ rộng thanh accent bar bên trái
_SEP_H       = 1                               # chiều cao separator
_ITEM_GAP    = 2                               # gap giữa các item
_ICON_LEFT   = _NAV_PAD + (_BTN_H - _ICON_SIZE) // 2  # icon center X trong vùng btn
_NAV_ICON_LEFT = _NAV_PAD + (_BTN_H - _NAV_ICON_SIZE) // 2  # nav icon center X
_TEXT_LEFT   = _NAV_PAD + _BTN_H + theme.SPACING_SM    # text bắt đầu sau icon + gap
_TEXT_VISIBLE_THRESHOLD = _W_COLLAPSED + 20    # width tối thiểu để vẽ text
_HOVER_RADIUS = 4                              # border-radius cho hover/active bg
_TOGGLE_GAP   = 6                              # gap giữa toggle button và nav items


def _load_pixmap(path: str | Path, size: int = _ICON_SIZE) -> QPixmap | None:
    """Load SVG → QPixmap tại kích thước chính xác. Trả về None nếu thất bại."""
    try:
        from PyQt6.QtSvg import QSvgRenderer
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        QSvgRenderer(str(path)).render(painter)
        painter.end()
        if not px.isNull():
            return px
    except Exception as e:
        _logger.debug("SVG render failed for %s: %s", path, e)
    # Fallback: load qua QIcon
    icon = QIcon(str(path))
    if not icon.isNull():
        return icon.pixmap(QSize(size, size))
    return None


def _tinted_pixmap(src: QPixmap, color: QColor) -> QPixmap:
    """Tô màu pixmap theo color (giữ alpha channel). Dùng để icon theo palette."""
    tinted = QPixmap(src.size())
    tinted.fill(Qt.GlobalColor.transparent)
    p = QPainter(tinted)
    p.drawPixmap(0, 0, src)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(tinted.rect(), color)
    p.end()
    return tinted


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class _NavItem:
    """Một mục nav trong sidebar."""
    identifier: str
    text: str
    pixmap: QPixmap | None = None
    checked: bool = False


@dataclass
class _Separator:
    """Một đường kẻ phân cách."""
    pass


# Union type cho các phần tử trong sidebar
_Entry = _NavItem | _Separator


class CollapsibleSidebar(QWidget):
    """
    Collapsible sidebar — custom painted, zero child widgets.

    Mọi thứ (background, accent bar, icon, text, hover, separator) được vẽ
    trong paintEvent. Không có QLayout, không có widget con → animation trên
    minimumWidth/maximumWidth KHÔNG BAO GIỜ gây layout recalc → icon cố định.

    Signals:
        toggled(bool)         — True=expanded, False=collapsed
        button_clicked(str)   — identifier của button được click
        page_changed(QWidget) — tương thích với QStackedWidget
    """

    toggled        = pyqtSignal(bool)
    button_clicked = pyqtSignal(str)
    page_changed   = pyqtSignal(QWidget)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._is_expanded = True
        self._entries: list[_Entry] = []
        self._bottom_entries: list[_Entry] = []   # items pinned to bottom
        self._page_map: dict[str, QWidget] = {}  # identifier → widget
        self._next_id = 0                         # auto-increment for stable IDs
        self._hover_index: int = -1               # -2 = hover trên toggle btn
        self._rects_cache: list[tuple[_Entry, QRect, bool]] | None = None
        self._rects_cache_w: int = -1             # width khi cache được tạo
        self._rects_cache_h: int = -1             # height khi cache được tạo

        # Toggle button icons
        self._px_menu = _load_pixmap("icons/material/menu.svg")
        self._px_menu_open = _load_pixmap("icons/material/menu_open.svg")

        self.setFixedWidth(_W_EXPANDED)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._setup_animation()

    # ── Animation ─────────────────────────────────────────────────────────────

    def _setup_animation(self) -> None:
        # QParallelAnimationGroup đảm bảo min và max luôn đồng bộ
        # trong cùng 1 frame — không bao giờ lệch nhau
        self._anim_group = QParallelAnimationGroup(self)

        self._anim_min = QPropertyAnimation(self, b"minimumWidth")
        self._anim_min.setDuration(_ANIM_MS)
        self._anim_min.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(_ANIM_MS)
        self._anim_max.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_group.addAnimation(self._anim_min)
        self._anim_group.addAnimation(self._anim_max)

    # ── Public API (giữ nguyên interface cũ 100%) ─────────────────────────────

    def add_button(self, identifier: str, text: str,
                   icon_path: str | Path | None = None) -> None:
        """Thêm nav button. identifier dùng cho button_clicked signal."""
        pixmap = _load_pixmap(icon_path, _NAV_ICON_SIZE) if icon_path else None
        self._entries.append(_NavItem(identifier=identifier, text=text, pixmap=pixmap))
        self._invalidate_rects()
        self.update()

    def add_item(self, icon: str, text: str, widget: QWidget) -> None:
        """Tương thích app_window.py. Tự emit page_changed khi click."""
        ident = f"_nav_{self._next_id}"
        self._next_id += 1
        self.add_button(ident, text, icon)
        self._page_map[ident] = widget
        # Item đầu tiên tự active
        nav_items = [e for e in self._entries if isinstance(e, _NavItem)]
        if len(nav_items) == 1:
            nav_items[0].checked = True
            self.page_changed.emit(widget)

    def add_item_bottom(self, icon: str, text: str, widget: QWidget) -> None:
        """Thêm item ghim dưới cùng sidebar (ví dụ: Settings)."""
        ident = f"_nav_{self._next_id}"
        self._next_id += 1
        pixmap = _load_pixmap(icon, _NAV_ICON_SIZE) if icon else None
        item = _NavItem(identifier=ident, text=text, pixmap=pixmap)
        self._bottom_entries.append(item)
        self._page_map[ident] = widget
        self._invalidate_rects()
        self.update()

    def add_separator(self) -> None:
        self._entries.append(_Separator())
        self._invalidate_rects()
        self.update()

    def toggle(self) -> None:
        self._is_expanded = not self._is_expanded
        target = _W_EXPANDED if self._is_expanded else _W_COLLAPSED

        self._anim_group.stop()

        current = self.width()
        self._anim_min.setStartValue(current)
        self._anim_min.setEndValue(target)
        self._anim_max.setStartValue(current)
        self._anim_max.setEndValue(target)

        self._anim_group.start()

        self.toggled.emit(self._is_expanded)

    def collapse(self) -> None:
        if self._is_expanded:
            self.toggle()

    def expand(self) -> None:
        if not self._is_expanded:
            self.toggle()

    def is_expanded(self) -> bool:
        return self._is_expanded

    def set_active_button(self, identifier: str) -> None:
        for entry in self._entries + self._bottom_entries:
            if isinstance(entry, _NavItem):
                entry.checked = (entry.identifier == identifier)
        self.update()

    def set_current(self, widget: QWidget) -> None:
        for ident, w in self._page_map.items():
            if w is widget:
                self._select(ident)
                return

    def update_texts(self, widget_text_map: dict[QWidget, str]) -> None:
        """Update display text of nav items by their associated widget.
        Identifiers remain stable — only display text changes."""
        for entry in self._entries + self._bottom_entries:
            if not isinstance(entry, _NavItem):
                continue
            widget = self._page_map.get(entry.identifier)
            if widget and widget in widget_text_map:
                entry.text = widget_text_map[widget]
        self.update()

    def cleanup(self) -> None:
        self._anim_group.stop()

    # ── Geometry helpers ──────────────────────────────────────────────────────

    def _toggle_rect(self) -> QRect:
        """Rect cho toggle button — cùng vị trí X, kích thước như nav items."""
        return QRect(0, _NAV_PAD, self.width(), _BTN_H)

    def _item_rects(self) -> list[tuple[_Entry, QRect, bool]]:
        """Tính toán vị trí Y — cached, chỉ rebuild khi width hoặc entries thay đổi.

        Returns list of (entry, rect, has_next_nav) — has_next_nav=True nếu phía sau
        còn NavItem (dùng để quyết định vẽ separator line hay không).

        Top entries flow top-down, bottom entries flow bottom-up.
        """
        w = self.width()
        h = self.height()
        if self._rects_cache is not None and self._rects_cache_w == w and self._rects_cache_h == h:
            return self._rects_cache
        result: list[tuple[_Entry, QRect, bool]] = []

        # Top entries
        y = _NAV_PAD + _BTN_H + _TOGGLE_GAP
        for entry in self._entries:
            if isinstance(entry, _Separator):
                rect = QRect(0, y, w, _SEP_H + _ITEM_GAP * 2)
                result.append((entry, rect, False))
                y += _SEP_H + _ITEM_GAP * 2
            else:
                rect = QRect(0, y, w, _BTN_H)
                result.append((entry, rect, False))
                y += _BTN_H + _ITEM_GAP

        # Bottom entries — positioned from bottom up
        if self._bottom_entries:
            by = h - _NAV_PAD
            for entry in reversed(self._bottom_entries):
                by -= _BTN_H
                rect = QRect(0, by, w, _BTN_H)
                result.append((entry, rect, False))
                by -= _ITEM_GAP

        # Pre-compute has_next_nav for top entries only
        top_count = len(self._entries)
        seen_nav_after = False
        for j in range(top_count - 1, -1, -1):
            entry, rect, _ = result[j]
            if isinstance(entry, _NavItem):
                result[j] = (entry, rect, seen_nav_after)
                seen_nav_after = True
        self._rects_cache = result
        self._rects_cache_w = w
        self._rects_cache_h = h
        return result

    def _invalidate_rects(self) -> None:
        """Gọi khi entries thay đổi."""
        self._rects_cache = None

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self._invalidate_rects()
        super().resizeEvent(event)

    def _hit_test(self, y: int) -> int:
        """Trả về index: -2 = toggle button, >=0 = NavItem index, -1 = nothing."""
        if self._toggle_rect().contains(0, y):
            return -2
        for i, (entry, rect, _) in enumerate(self._item_rects()):
            if isinstance(entry, _NavItem) and rect.contains(0, y):
                return i
        return -1

    # ── Events ────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        from widgets.tooltip import Tooltip
        Tooltip.hide_immediate()
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self._hit_test(int(event.position().y()))
            if idx == -2:
                self.toggle()
            elif idx >= 0:
                entry, _, _ = self._item_rects()[idx]
                if isinstance(entry, _NavItem):
                    self._select(entry.identifier)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        idx = self._hit_test(int(event.position().y()))
        if idx != self._hover_index:
            self._hover_index = idx
            self.update()
            self._update_tooltip(idx)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        if self._hover_index != -1:
            self._hover_index = -1
            self.update()
        from widgets.tooltip import Tooltip
        Tooltip.hide_immediate()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        pal = self.palette()
        w = self.width()
        h = self.height()

        # ── Background trắng ──────────────────────────────────────────────
        p.fillRect(self.rect(), pal.base())

        # ── Right border — 2 lines giống Fusion Sunken (dark + light) ────
        #   Line 1: pal.dark() (shadow line)
        #   Line 2: pal.light() (highlight line) — ngay bên phải
        # Kết quả giống hệt QFrame.VLine + Sunken nhưng không có artifact
        p.setPen(QPen(pal.dark().color(), 0))
        p.drawLine(w - 2, 0, w - 2, h)
        p.setPen(QPen(pal.light().color(), 0))
        p.drawLine(w - 1, 0, w - 1, h)
        sep_pen = QPen(pal.mid().color(), 0)
        icon_tint = pal.text().color()  # tint icons theo palette

        # ── Toggle button (trên cùng, cùng style hover như nav items) ────
        t_rect = self._toggle_rect()
        is_toggle_hover = (self._hover_index == -2)
        if is_toggle_hover:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal.midlight().color())
            p.drawRoundedRect(
                _NAV_PAD, t_rect.y(), w - _NAV_PAD * 2, _BTN_H,
                _HOVER_RADIUS, _HOVER_RADIUS,
            )
            p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        t_px = self._px_menu if self._is_expanded else self._px_menu_open
        if t_px:
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            p.drawPixmap(_ICON_LEFT, t_rect.y() + (_BTN_H - _ICON_SIZE) // 2,
                         _tinted_pixmap(t_px, icon_tint))

        # ── Separator dưới toggle ────────────────────────────────────────
        sep_y = t_rect.y() + _BTN_H + _TOGGLE_GAP // 2
        p.setPen(sep_pen)
        p.drawLine(_NAV_PAD, sep_y, w - _NAV_PAD, sep_y)

        # ── Nav items ────────────────────────────────────────────────────
        item_rects = self._item_rects()
        accent_color = pal.highlight().color()
        text_color = pal.text().color()
        hover_bg = pal.midlight().color()
        active_bg = QColor(accent_color)
        active_bg.setAlpha(30)
        draw_text = w > _TEXT_VISIBLE_THRESHOLD
        hover_idx = self._hover_index

        p.setFont(theme.font(bold=True))

        for i, (entry, rect, has_next) in enumerate(item_rects):
            if isinstance(entry, _Separator):
                continue  # _Separator từ MENU vẫn tạo khoảng cách, không vẽ thêm

            ry = rect.y()

            # ── Hover / Active background ─────────────────────────────
            is_hover = (i == hover_idx and not entry.checked)
            if is_hover or entry.checked:
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(hover_bg if is_hover else active_bg)
                p.drawRoundedRect(
                    _NAV_PAD, ry, w - _NAV_PAD * 2, _BTN_H,
                    _HOVER_RADIUS, _HOVER_RADIUS,
                )
                p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

            # ── Accent bar bên trái (chỉ khi active) ─────────────────
            if entry.checked:
                bar_h = _BTN_H - 12
                bar_y = ry + (_BTN_H - bar_h) // 2
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setBrush(accent_color)
                p.drawRoundedRect(
                    QRectF(_NAV_PAD, bar_y, _ACCENT_W, bar_h),
                    _ACCENT_W / 2, _ACCENT_W / 2,
                )
                p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

            # ── Icon (vị trí tuyệt đối — không bao giờ thay đổi) ─────
            if entry.pixmap:
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                ic_color = accent_color if entry.checked else icon_tint
                p.drawPixmap(_NAV_ICON_LEFT, ry + (_BTN_H - _NAV_ICON_SIZE) // 2,
                             _tinted_pixmap(entry.pixmap, ic_color))

            # ── Text (chỉ vẽ khi đủ rộng) ────────────────────────────
            if draw_text:
                p.setPen(accent_color if entry.checked else text_color)
                p.drawText(
                    _TEXT_LEFT, ry, w - _TEXT_LEFT - _NAV_PAD, _BTN_H,
                    Qt.AlignmentFlag.AlignVCenter, entry.text.upper(),
                )

            # ── Separator dưới nav item (pre-computed) ───────────────
            if has_next:
                p.setPen(sep_pen)
                p.drawLine(
                    _NAV_PAD, ry + _BTN_H + _ITEM_GAP // 2,
                    w - _NAV_PAD, ry + _BTN_H + _ITEM_GAP // 2,
                )

        # ── Separator trên bottom entries ──────────────────────────
        if self._bottom_entries:
            top_count = len(self._entries)
            # Find first bottom entry rect
            for i, (entry, rect, _) in enumerate(item_rects):
                if i >= top_count and isinstance(entry, _NavItem):
                    sep_by = rect.y() - _TOGGLE_GAP // 2 - _ITEM_GAP
                    p.setPen(sep_pen)
                    p.drawLine(_NAV_PAD, sep_by, w - _NAV_PAD, sep_by)
                    break

        p.end()

    # ── Tooltip ─────────────────────────────────────────────────────────────

    def _update_tooltip(self, idx: int) -> None:
        """Show/hide tooltip for the hovered sidebar item."""
        from widgets.tooltip import Tooltip

        # Only show tooltips when sidebar is collapsed (no text visible)
        if self.width() > _TEXT_VISIBLE_THRESHOLD:
            Tooltip.hide_immediate()
            return

        if idx == -1:
            Tooltip.hide_immediate()
            return

        # Get text for the hovered item
        if idx == -2:
            # Toggle button — no tooltip needed
            Tooltip.hide_immediate()
            return

        entry, rect, _ = self._item_rects()[idx]
        if not isinstance(entry, _NavItem):
            Tooltip.hide_immediate()
            return

        # Convert local rect to global coords
        global_top_left = self.mapToGlobal(QPoint(rect.x(), rect.y()))
        global_rect = QRect(global_top_left, rect.size())

        Tooltip.show_at_rect(self, global_rect, entry.text, position="right")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _select(self, identifier: str) -> None:
        """Chọn một item theo identifier."""
        for entry in self._entries + self._bottom_entries:
            if isinstance(entry, _NavItem):
                entry.checked = (entry.identifier == identifier)
        self.update()
        self.button_clicked.emit(identifier)
        # Emit page_changed nếu có widget tương ứng
        widget = self._page_map.get(identifier)
        if widget is not None:
            self.page_changed.emit(widget)
