# Design: Collapsible Sidebar Navigation

Date: 2026-03-05

## Context

TEMPLE-PYQT6 currently uses `QTabWidget` for navigation. As apps grow to 8-15+ pages,
tabs become cramped and unscalable. A collapsible sidebar is the standard pattern for
admin desktop applications.

## Requirements

- Sidebar on the left, content area on the right
- Collapsed: 48px wide, icon-only with hover tooltips
- Expanded: 200px wide, icon + text label
- Toggle button in sidebar footer (arrows)
- Menu defined as config list in `app_window.py` — easy to add/reorder/remove pages
- Animation: `QPropertyAnimation` on width (200 <-> 48px)
- `BaseTab` unchanged — existing tabs work without modification

## Approach

**QSplitter + CollapsibleSidebar widget** (Approach 1 of 3 considered)

- `QSplitter` (handle hidden) divides window into sidebar + content
- `CollapsibleSidebar(QWidget)` handles item rendering and animation
- `QStackedWidget` holds all tab pages, sidebar controls which is visible
- Rejected: manual QHBoxLayout (glitchy animation), QDockWidget (no icon-only collapse)

## Architecture

```
AppWindow (QMainWindow)
├── QToolBar — toggle button + app actions
├── central widget
│   └── QSplitter (horizontal, handle hidden, not user-resizable)
│       ├── CollapsibleSidebar  [widgets/sidebar.py]
│       │   ├── scroll area with SidebarItem buttons
│       │   └── toggle button at bottom
│       └── QStackedWidget — content pages
└── QStatusBar
```

## Files

| File | Change |
|------|--------|
| `widgets/sidebar.py` | Create — `CollapsibleSidebar`, `SidebarItem` |
| `core/app_window.py` | Modify — replace `QTabWidget` with sidebar layout |
| `CLAUDE.md` | Update — add sidebar to shared components table |

## API

```python
# widgets/sidebar.py
class CollapsibleSidebar(QWidget):
    page_changed = pyqtSignal(QWidget)

    def add_item(self, icon: str, text: str, widget: QWidget) -> None: ...
    def add_separator(self) -> None: ...
    def toggle(self) -> None: ...
    def is_expanded(self) -> bool: ...
    def set_current(self, widget: QWidget) -> None: ...
```

## Menu Config (app_window.py)

```python
MENU = [
    {"icon": "icons/layui/home.svg",  "text": "Trang chu", "tab": HomeTab},
    None,  # separator
    {"icon": "icons/layui/table.svg", "text": "Vi du",     "tab": ExampleTab},
]
```

## Visual Behavior

- **Expanded (200px):** icon 20px + text, active item highlighted
- **Collapsed (48px):** icon only, centered; tooltip shows text on hover
- **Animation:** 150ms, QEasingCurve.OutCubic
- **Active highlight:** QPalette highlight color (adapts to theme)
- **Toggle button:** arrow icon at bottom of sidebar, flips on toggle

## Constraints

- `SIDEBAR_WIDTH = 200` and `SIDEBAR_COLLAPSED_WIDTH = 48` defined in `core/theme.py`
- No hardcoded colors — use QPalette roles
- No hardcoded sizes — use theme constants
- Animation runs on main thread (width change is cheap, no blocking)
