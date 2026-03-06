# Collapsible Sidebar Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace QTabWidget in AppWindow with a collapsible sidebar (200px expanded / 48px icon-only) + QStackedWidget layout.

**Architecture:** `CollapsibleSidebar(QWidget)` in `widgets/sidebar.py` renders menu items as icon+text buttons; `QPropertyAnimation` animates width between 200px and 48px; `QSplitter` (handle hidden) holds sidebar + `QStackedWidget`; menu defined as config list `MENU` in `app_window.py`.

**Tech Stack:** PyQt6 — QPropertyAnimation, QSplitter, QStackedWidget, QToolButton, SVG icons from `icons/layui/`

---

### Task 1: Add `SIDEBAR_COLLAPSED_WIDTH` constant to `core/theme.py`

**Files:**
- Modify: `core/theme.py:32`

**Step 1: Add constant**

In `core/theme.py`, after line `SIDEBAR_WIDTH = 200`, add:

```python
SIDEBAR_COLLAPSED_WIDTH = 48
SIDEBAR_ANIM_MS  = 150   # animation duration in milliseconds
```

**Step 2: Verify**

Open Python REPL in project dir:
```python
from core import theme
assert theme.SIDEBAR_WIDTH == 200
assert theme.SIDEBAR_COLLAPSED_WIDTH == 48
assert theme.SIDEBAR_ANIM_MS == 150
print("OK")
```
Expected: `OK`

---

### Task 2: Create `widgets/sidebar.py` — `CollapsibleSidebar`

**Files:**
- Create: `widgets/sidebar.py`

**Step 1: Write the file**

```python
"""
widgets/sidebar.py
Collapsible sidebar navigation widget.

Usage:
    from widgets.sidebar import CollapsibleSidebar

    sidebar = CollapsibleSidebar()
    sidebar.add_item("icons/layui/home.svg", "Trang chu", home_widget)
    sidebar.add_separator()
    sidebar.add_item("icons/layui/user.svg", "Nhan vien", nhanvien_widget)
    sidebar.page_changed.connect(stack.setCurrentWidget)
    sidebar.toggle()          # expand / collapse
    sidebar.is_expanded()     # -> bool
"""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolButton,
    QLabel, QSizePolicy, QFrame, QScrollArea,
)
from PyQt6.QtCore import (
    Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtSignal,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvgWidgets import QSvgWidget
from core import theme


# ── SVG icon helper ───────────────────────────────────────────────────────────

def _make_icon(svg_path: str, size: int = 20) -> QIcon:
    """Load SVG as QIcon. Falls back to empty icon on error."""
    try:
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        from PyQt6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(svg_path)
        renderer.render(painter)
        painter.end()
        return QIcon(px)
    except Exception:
        return QIcon()


# ── Single nav item button ────────────────────────────────────────────────────

class _SidebarButton(QToolButton):
    """One navigation item: icon + text, highlights when active."""

    ICON_SIZE = 20

    def __init__(self, icon_path: str, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._icon_path = icon_path
        self._text = text
        self._active = False

        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIcon(_make_icon(icon_path, self.ICON_SIZE))
        self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.setText(text)
        self.setToolTip(text)
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._apply_style(active=False)

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style(active)

    def set_collapsed(self, collapsed: bool) -> None:
        if collapsed:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        else:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

    def _apply_style(self, active: bool) -> None:
        palette = self.palette()
        if active:
            bg = palette.highlight().color().name()
            fg = palette.highlightedText().color().name()
        else:
            bg = "transparent"
            fg = palette.windowText().color().name()

        self.setStyleSheet(f"""
            QToolButton {{
                background: {bg};
                color: {fg};
                border: none;
                border-radius: 4px;
                padding: 6px 8px;
                text-align: left;
                font-size: {theme.FONT_SIZE}pt;
                font-family: {theme.FONT_FAMILY};
            }}
            QToolButton:hover {{
                background: {palette.highlight().color().lighter(150).name()};
                color: {palette.highlightedText().color().name()};
            }}
        """)


# ── Separator ─────────────────────────────────────────────────────────────────

class _SidebarSep(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setFixedHeight(1)


# ── Main sidebar widget ───────────────────────────────────────────────────────

class CollapsibleSidebar(QWidget):
    """
    Collapsible sidebar: expanded=200px (icon+text), collapsed=48px (icon only).
    Animate via QPropertyAnimation on minimumWidth / maximumWidth.
    """

    page_changed = pyqtSignal(QWidget)   # emitted when user clicks a nav item

    _EXPANDED  = theme.SIDEBAR_WIDTH
    _COLLAPSED = theme.SIDEBAR_COLLAPSED_WIDTH
    _ANIM_MS   = theme.SIDEBAR_ANIM_MS

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._expanded = True
        self._buttons: list[tuple[_SidebarButton, QWidget]] = []  # (btn, page)
        self._active_btn: _SidebarButton | None = None

        self.setFixedWidth(self._EXPANDED)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Animation on the widget's maximumWidth (simplest stable approach)
        self._anim = QPropertyAnimation(self, b"maximumWidth")
        self._anim.setDuration(self._ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self._on_anim_finished)

        self._anim_min = QPropertyAnimation(self, b"minimumWidth")
        self._anim_min.setDuration(self._ANIM_MS)
        self._anim_min.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(*theme.MARGIN_ZERO)
        root.setSpacing(theme.SPACING_XS)

        # Scroll area holds nav items
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._nav_widget = QWidget()
        self._nav_layout = QVBoxLayout(self._nav_widget)
        self._nav_layout.setContentsMargins(theme.SPACING_SM, theme.SPACING_SM,
                                            theme.SPACING_SM, theme.SPACING_SM)
        self._nav_layout.setSpacing(theme.SPACING_XS)
        self._nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._nav_widget)
        root.addWidget(self._scroll, 1)

        # Toggle button at bottom
        self._toggle_btn = QToolButton()
        self._toggle_btn.setIcon(_make_icon("icons/layui/left.svg", 16))
        self._toggle_btn.setIconSize(QSize(16, 16))
        self._toggle_btn.setToolTip("Thu gon / Mo rong")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._toggle_btn.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 6px;
                border-top: 1px solid palette(mid);
            }
            QToolButton:hover { background: palette(midlight); }
        """)
        self._toggle_btn.clicked.connect(self.toggle)
        root.addWidget(self._toggle_btn)

    # ── Public API ────────────────────────────────────────────────────────────

    def add_item(self, icon: str, text: str, widget: QWidget) -> None:
        """Add a navigation item linked to a page widget."""
        btn = _SidebarButton(icon, text, self._nav_widget)
        btn.clicked.connect(lambda: self._on_item_clicked(btn, widget))
        self._nav_layout.addWidget(btn)
        self._buttons.append((btn, widget))

        # Auto-activate first item
        if len(self._buttons) == 1:
            self._activate(btn, widget)

    def add_separator(self) -> None:
        """Add a visual separator line."""
        sep = _SidebarSep(self._nav_widget)
        self._nav_layout.addWidget(sep)

    def toggle(self) -> None:
        """Expand or collapse the sidebar."""
        if self._expanded:
            self._animate_to(self._COLLAPSED)
            self._expanded = False
            self._set_buttons_collapsed(True)
            self._toggle_btn.setIcon(_make_icon("icons/layui/right.svg", 16))
        else:
            self._animate_to(self._EXPANDED)
            self._expanded = True
            self._set_buttons_collapsed(False)
            self._toggle_btn.setIcon(_make_icon("icons/layui/left.svg", 16))

    def is_expanded(self) -> bool:
        return self._expanded

    def set_current(self, widget: QWidget) -> None:
        """Programmatically activate the item linked to widget."""
        for btn, page in self._buttons:
            if page is widget:
                self._activate(btn, widget)
                return

    # ── Internal ──────────────────────────────────────────────────────────────

    def _animate_to(self, target: int) -> None:
        current = self.width()
        self._anim.setStartValue(current)
        self._anim.setEndValue(target)
        self._anim_min.setStartValue(current)
        self._anim_min.setEndValue(target)
        self._anim.start()
        self._anim_min.start()

    def _on_anim_finished(self) -> None:
        # Fix width after animation
        w = self._EXPANDED if self._expanded else self._COLLAPSED
        self.setFixedWidth(w)

    def _set_buttons_collapsed(self, collapsed: bool) -> None:
        for btn, _ in self._buttons:
            btn.set_collapsed(collapsed)

    def _on_item_clicked(self, btn: _SidebarButton, widget: QWidget) -> None:
        self._activate(btn, widget)
        self.page_changed.emit(widget)

    def _activate(self, btn: _SidebarButton, widget: QWidget) -> None:
        if self._active_btn:
            self._active_btn.set_active(False)
        btn.set_active(True)
        self._active_btn = btn
        self.page_changed.emit(widget)
```

**Step 2: Verify import**

```bash
cd "C:\Users\Admin\Desktop\TEMPLE-PYQT6"
python -c "from widgets.sidebar import CollapsibleSidebar; print('OK')"
```
Expected: `OK`

---

### Task 3: Rewrite `_build_central()` in `core/app_window.py`

**Files:**
- Modify: `core/app_window.py`

**Step 1: Update imports at top of file**

Replace the existing imports block with:

```python
"""
core/app_window.py — Main window cua ung dung
Chua: MenuBar, ToolBar, StatusBar, Sidebar + StackedWidget
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QStatusBar,
    QToolBar, QSplitter,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from core import theme
from core.base_widgets import vbox
from dialogs.about_dialog import AboutDialog
from utils.settings import settings
from widgets.sidebar import CollapsibleSidebar

# Import cac tab cua du an
from tabs.home_tab    import HomeTab
from tabs.example_tab import ExampleTab
```

**Step 2: Add MENU config below imports**

```python
# ── Menu config — them/xoa/reorder tai day ────────────────────────────────────
MENU: list[dict | None] = [
    {"icon": "icons/layui/home.svg",  "text": "Trang chu", "tab": HomeTab},
    None,  # separator
    {"icon": "icons/layui/table.svg", "text": "Vi du",     "tab": ExampleTab},
    # Them muc moi:
    # {"icon": "icons/layui/user.svg", "text": "Nhan vien", "tab": NhanVienTab},
]
```

**Step 3: Replace `_build_central()` method**

Replace the existing `_build_central` method body with:

```python
def _build_central(self) -> None:
    self._stack = QStackedWidget()
    self._sidebar = CollapsibleSidebar()

    # Build pages from MENU config
    for item in MENU:
        if item is None:
            self._sidebar.add_separator()
        else:
            page = item["tab"]()
            self._stack.addWidget(page)
            self._sidebar.add_item(item["icon"], item["text"], page)

    # Connect sidebar page changes to stack
    self._sidebar.page_changed.connect(self._stack.setCurrentWidget)

    # Splitter: sidebar | content
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setHandleWidth(0)          # hide the drag handle
    splitter.setChildrenCollapsible(False)
    splitter.addWidget(self._sidebar)
    splitter.addWidget(self._stack)
    splitter.setStretchFactor(0, 0)     # sidebar: fixed
    splitter.setStretchFactor(1, 1)     # content: stretch

    central = QWidget()
    lay = vbox(margins=theme.MARGIN_ZERO, spacing=0)
    lay.addWidget(splitter)
    central.setLayout(lay)
    self.setCentralWidget(central)
```

**Step 4: Update `_build_toolbar()` — add sidebar toggle button**

In `_build_toolbar`, add a toggle action as the first item:

```python
def _build_toolbar(self) -> None:
    tb = QToolBar("Main")
    tb.setMovable(False)
    self.addToolBar(tb)

    # Sidebar toggle (first action)
    self._toggle_act = QAction("|||", self)
    self._toggle_act.setToolTip("Mo/dong sidebar (Ctrl+\\)")
    self._toggle_act.setShortcut("Ctrl+\\")
    self._toggle_act.triggered.connect(lambda: self._sidebar.toggle())
    tb.addAction(self._toggle_act)
    tb.addSeparator()

    for label in ["New", "Open", "Save", "|", "Undo", "Redo"]:
        if label == "|":
            tb.addSeparator()
        else:
            tb.addAction(QAction(label, self))
```

**Step 5: Update statusbar to show page name**

In `_build_central`, after `self._sidebar.page_changed.connect(...)`, add:

```python
self._sidebar.page_changed.connect(
    lambda w: self.status.showMessage(
        next((m["text"] for m in MENU if m and m["tab"] == type(w)), "")
    )
)
```

**Step 6: Verify app launches**

```bash
cd "C:\Users\Admin\Desktop\TEMPLE-PYQT6"
python main.py
```

Expected: App opens, sidebar on left (200px), Home tab content on right. Clicking sidebar items switches pages. Toggle button collapses sidebar to 48px icon-only.

---

### Task 4: Update `CLAUDE.md` — add sidebar to shared components

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add sidebar row to widgets table**

In the `### widgets/` table, add a new row after `table_crud.py`:

```
| `sidebar.py` | `CollapsibleSidebar` | Sidebar nav đóng/mở thay QTabWidget |
```

**Step 2: Add import line to widgets import block**

```python
from widgets.sidebar import CollapsibleSidebar
```

**Step 3: Add usage note in MENU config section**

After the widgets table, add:

```
### Thêm menu item vào sidebar

Sửa list `MENU` trong `core/app_window.py`:
```python
MENU = [
    {"icon": "icons/layui/home.svg",  "text": "Trang chu", "tab": HomeTab},
    None,  # separator
    {"icon": "icons/layui/user.svg",  "text": "Nhan vien", "tab": NhanVienTab},
    {"icon": "icons/layui/set.svg",   "text": "Cai dat",   "tab": CaiDatTab},
]
```
Moi entry la dict `{icon, text, tab}`. `None` = separator. Thu tu = thu tu hien thi.
```

---

### Task 5: Edge cases and polish

**Files:**
- Modify: `widgets/sidebar.py`

**Step 1: Handle missing SVG icons gracefully**

The `_make_icon` function already has a try/except. Verify it with a bad path:

```python
from widgets.sidebar import _make_icon
icon = _make_icon("icons/layui/nonexistent.svg")
assert icon is not None   # returns empty QIcon, not crash
print("OK")
```

**Step 2: Verify toggle keyboard shortcut**

Launch app, press `Ctrl+\` — sidebar should toggle.

**Step 3: Verify tooltip in collapsed state**

Collapse sidebar, hover over an icon — tooltip should show the page text.

**Step 4: Verify window geometry saved/restored across restarts**

Close app, reopen — window should restore to same size/position (handled by existing `settings.save_window` / `settings.restore_window`).

---

### Summary of all changed files

| File | Change |
|------|--------|
| `core/theme.py` | +2 constants: `SIDEBAR_COLLAPSED_WIDTH`, `SIDEBAR_ANIM_MS` |
| `widgets/sidebar.py` | New file: `CollapsibleSidebar`, `_SidebarButton`, `_SidebarSep` |
| `core/app_window.py` | Replace QTabWidget with QSplitter+CollapsibleSidebar+QStackedWidget |
| `CLAUDE.md` | Add sidebar to shared components docs |
