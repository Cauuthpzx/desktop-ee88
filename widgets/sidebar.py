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
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect, QRectF, QSize,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QCursor, QMouseEvent
from core import theme


# ── Constants ─────────────────────────────────────────────────────────────────
_W_EXPANDED  = theme.SIDEBAR_WIDTH            # 200
_W_COLLAPSED = theme.SIDEBAR_COLLAPSED_WIDTH   # 48
_ICON_SIZE   = 20
_BTN_H       = 36                              # chiều cao mỗi item
_ANIM_MS     = theme.SIDEBAR_ANIM_MS           # 150
_NAV_PAD     = (_W_COLLAPSED - _BTN_H) // 2    # padding trái = (48-36)/2 = 6
_ACCENT_W    = 3                               # độ rộng thanh accent bar bên trái
_SEP_H       = 1                               # chiều cao separator
_ITEM_GAP    = 2                               # gap giữa các item
_ICON_LEFT   = _NAV_PAD + (_BTN_H - _ICON_SIZE) // 2  # icon center X trong vùng btn
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
    except Exception:
        pass
    # Fallback: load qua QIcon
    icon = QIcon(str(path))
    if not icon.isNull():
        return icon.pixmap(QSize(size, size))
    return None


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
        self._page_map: dict[str, QWidget] = {}  # identifier → widget
        self._hover_index: int = -1               # -2 = hover trên toggle btn

        # Toggle button icons
        self._px_menu = _load_pixmap("icons/menu.svg")
        self._px_menu_open = _load_pixmap("icons/menu_open.svg")

        self.setFixedWidth(_W_EXPANDED)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._setup_animation()

    # ── Animation ─────────────────────────────────────────────────────────────

    def _setup_animation(self) -> None:
        self._anim_min = QPropertyAnimation(self, b"minimumWidth")
        self._anim_min.setDuration(_ANIM_MS)
        self._anim_min.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._anim_max = QPropertyAnimation(self, b"maximumWidth")
        self._anim_max.setDuration(_ANIM_MS)
        self._anim_max.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Public API (giữ nguyên interface cũ 100%) ─────────────────────────────

    def add_button(self, identifier: str, text: str,
                   icon_path: str | Path | None = None) -> None:
        """Thêm nav button. identifier dùng cho button_clicked signal."""
        pixmap = _load_pixmap(icon_path) if icon_path else None
        self._entries.append(_NavItem(identifier=identifier, text=text, pixmap=pixmap))
        self.update()

    def add_item(self, icon: str, text: str, widget: QWidget) -> None:
        """Tương thích app_window.py. Tự emit page_changed khi click."""
        self.add_button(text, text, icon)
        self._page_map[text] = widget
        # Item đầu tiên tự active
        nav_items = [e for e in self._entries if isinstance(e, _NavItem)]
        if len(nav_items) == 1:
            nav_items[0].checked = True
            self.page_changed.emit(widget)

    def add_separator(self) -> None:
        self._entries.append(_Separator())
        self.update()

    def toggle(self) -> None:
        self._is_expanded = not self._is_expanded
        target = _W_EXPANDED if self._is_expanded else _W_COLLAPSED

        self._anim_min.stop()
        self._anim_max.stop()

        self._anim_min.setStartValue(self.width())
        self._anim_min.setEndValue(target)
        self._anim_max.setStartValue(self.width())
        self._anim_max.setEndValue(target)

        self._anim_min.start()
        self._anim_max.start()

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
        for entry in self._entries:
            if isinstance(entry, _NavItem):
                entry.checked = (entry.identifier == identifier)
        self.update()

    def set_current(self, widget: QWidget) -> None:
        for ident, w in self._page_map.items():
            if w is widget:
                self._select(ident)
                return

    def cleanup(self) -> None:
        self._anim_min.stop()
        self._anim_max.stop()

    # ── Geometry helpers ──────────────────────────────────────────────────────

    def _toggle_rect(self) -> QRect:
        """Rect cho toggle button — cùng vị trí X, kích thước như nav items."""
        return QRect(0, _NAV_PAD, self.width(), _BTN_H)

    def _item_rects(self) -> list[tuple[_Entry, QRect]]:
        """Tính toán vị trí Y của từng entry (sau toggle button)."""
        result: list[tuple[_Entry, QRect]] = []
        y = _NAV_PAD + _BTN_H + _TOGGLE_GAP  # sau toggle button
        w = self.width()
        for entry in self._entries:
            if isinstance(entry, _Separator):
                rect = QRect(0, y, w, _SEP_H + _ITEM_GAP * 2)
                result.append((entry, rect))
                y += _SEP_H + _ITEM_GAP * 2
            else:
                rect = QRect(0, y, w, _BTN_H)
                result.append((entry, rect))
                y += _BTN_H + _ITEM_GAP
        return result

    def _hit_test(self, y: int) -> int:
        """Trả về index: -2 = toggle button, >=0 = NavItem index, -1 = nothing."""
        if self._toggle_rect().contains(0, y):
            return -2
        for i, (entry, rect) in enumerate(self._item_rects()):
            if isinstance(entry, _NavItem) and rect.contains(0, y):
                return i
        return -1

    # ── Events ────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self._hit_test(int(event.position().y()))
            if idx == -2:
                self.toggle()
            elif idx >= 0:
                entry = self._entries[idx]
                if isinstance(entry, _NavItem):
                    self._select(entry.identifier)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        idx = self._hit_test(int(event.position().y()))
        if idx != self._hover_index:
            self._hover_index = idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        if self._hover_index != -1:
            self._hover_index = -1
            self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pal = self.palette()
        w = self.width()
        h = self.height()

        # ── Background trắng ──────────────────────────────────────────────
        p.fillRect(self.rect(), pal.base())

        # ── Right border — pal.mid(), cosmetic pen, khớp Fusion toolbar ──
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setPen(QPen(pal.mid().color(), 0))
        p.drawLine(w - 1, 0, w - 1, h)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # ── Toggle button (trên cùng, cùng style hover như nav items) ────
        t_rect = self._toggle_rect()
        t_item_rect = QRect(_NAV_PAD, t_rect.y(), w - _NAV_PAD * 2, _BTN_H)
        is_toggle_hover = (self._hover_index == -2)
        if is_toggle_hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pal.midlight().color())
            p.drawRoundedRect(t_item_rect, _HOVER_RADIUS, _HOVER_RADIUS)

        t_px = self._px_menu if self._is_expanded else self._px_menu_open
        if t_px:
            p.drawPixmap(_ICON_LEFT, t_rect.y() + (_BTN_H - _ICON_SIZE) // 2, t_px)

        # ── Separator dưới toggle ────────────────────────────────────────
        sep_pen = QPen(pal.mid().color(), 0)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        sep_y = t_rect.y() + _BTN_H + _TOGGLE_GAP // 2
        p.setPen(sep_pen)
        p.drawLine(_NAV_PAD, sep_y, w - _NAV_PAD, sep_y)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # ── Nav items ────────────────────────────────────────────────────
        item_rects = self._item_rects()
        accent_color = pal.highlight().color()
        text_color = pal.text().color()
        hover_bg = pal.midlight().color()
        active_bg = QColor(accent_color)
        active_bg.setAlpha(30)

        p.setFont(theme.font())

        for i, (entry, rect) in enumerate(item_rects):
            if isinstance(entry, _Separator):
                continue  # _Separator từ MENU vẫn tạo khoảng cách, không vẽ thêm

            # entry is _NavItem
            item_rect = QRect(_NAV_PAD, rect.y(), w - _NAV_PAD * 2, _BTN_H)

            # ── Hover background ──────────────────────────────────────
            is_hover = (i == self._hover_index and not entry.checked)
            if is_hover:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(hover_bg)
                p.drawRoundedRect(item_rect, _HOVER_RADIUS, _HOVER_RADIUS)

            # ── Active state: subtle bg + accent bar ──────────────────
            if entry.checked:
                # Subtle background
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(active_bg)
                p.drawRoundedRect(item_rect, _HOVER_RADIUS, _HOVER_RADIUS)

                # Accent bar bên trái
                bar_h = _BTN_H - 12  # bar ngắn hơn item một chút
                bar_y = rect.y() + (_BTN_H - bar_h) // 2
                bar_rect = QRectF(_NAV_PAD, bar_y, _ACCENT_W, bar_h)
                p.setBrush(accent_color)
                p.drawRoundedRect(bar_rect, _ACCENT_W / 2, _ACCENT_W / 2)

            # ── Icon (vị trí tuyệt đối — không bao giờ thay đổi) ─────
            if entry.pixmap:
                icon_x = _ICON_LEFT
                icon_y = rect.y() + (_BTN_H - _ICON_SIZE) // 2
                p.drawPixmap(icon_x, icon_y, entry.pixmap)

            # ── Text (chỉ vẽ khi đủ rộng) ────────────────────────────
            if w > _TEXT_VISIBLE_THRESHOLD:
                text_rect = QRect(
                    _TEXT_LEFT, rect.y(),
                    w - _TEXT_LEFT - _NAV_PAD, _BTN_H,
                )
                if entry.checked:
                    p.setPen(accent_color)
                else:
                    p.setPen(text_color)
                p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, entry.text)

            # ── Separator dưới mỗi nav item ─────────────────────────
            # Kiểm tra còn nav item phía sau không (bỏ qua _Separator)
            has_next = any(
                isinstance(e, _NavItem)
                for e, _ in item_rects[i + 1:]
            )
            if has_next:
                p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                line_y = rect.y() + _BTN_H + _ITEM_GAP // 2
                p.setPen(sep_pen)
                p.drawLine(_NAV_PAD, line_y, w - _NAV_PAD, line_y)
                p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        p.end()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _select(self, identifier: str) -> None:
        """Chọn một item theo identifier."""
        for entry in self._entries:
            if isinstance(entry, _NavItem):
                entry.checked = (entry.identifier == identifier)
        self.update()
        self.button_clicked.emit(identifier)
        # Emit page_changed nếu có widget tương ứng
        widget = self._page_map.get(identifier)
        if widget is not None:
            self.page_changed.emit(widget)
