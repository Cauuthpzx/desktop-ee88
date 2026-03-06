"""
widgets/table_crud.py
Table tích hợp sẵn: Toolbar (Thêm/Sửa/Xoá) + SearchBar + Table + Pagination + EmptyState.
Dùng để nhúng trực tiếp vào tab, không cần tự lắp từng phần.

Dùng:
    from widgets.table_crud import TableCrud

    self.crud = TableCrud(
        columns=["ID", "Tên", "Tuổi", "Vai trò"],
        on_add=self._on_add,
        on_edit=self._on_edit,
        on_delete=self._on_delete,
        on_search=self._on_search,       # optional
        on_page_change=self._load_page,  # optional
        page_size=20,
    )
    layout.addWidget(self.crud)

    # Load data:
    self.crud.load(data, keys=["id", "name", "age", "role"])

    # Update tổng số (dùng với phân trang server-side):
    self.crud.set_total(250)

    # Lấy ID dòng đang chọn:
    id_ = self.crud.selected_id()
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
)
from PyQt6.QtCore import pyqtSignal
from widgets.toolbar_widget import ContentToolbar
from widgets.pagination     import Pagination
from widgets.empty_state    import EmptyState
from utils.table_helper     import setup_table, load_table, get_selected_id
from core import theme
from core.i18n import t


class TableCrud(QWidget):
    selection_changed = pyqtSignal(bool)   # True nếu có dòng đang chọn

    def __init__(self,
                 columns: list[str],
                 on_add=None,
                 on_edit=None,
                 on_delete=None,
                 on_search=None,
                 on_page_change=None,
                 page_size: int = 20,
                 add_label:    str = "",
                 edit_label:   str = "",
                 delete_label: str = "",
                 search_placeholder: str = ""):
        super().__init__()
        self._columns   = columns
        self._page_size = page_size

        add_label    = add_label    or t("crud.add")
        edit_label   = edit_label   or t("crud.edit")
        delete_label = delete_label or t("crud.delete")
        search_placeholder = search_placeholder or t("crud.search")

        root = QVBoxLayout(self)
        root.setContentsMargins(*theme.MARGIN_ZERO)
        root.setSpacing(theme.SPACING_SM)

        # ── Toolbar ───────────────────────────────────────
        self._toolbar = ContentToolbar()
        self._toolbar.add_button(add_label,    on_add)
        self._toolbar.add_button(edit_label,   on_edit,   enabled=False)
        self._toolbar.add_button(delete_label, on_delete, enabled=False)
        self._toolbar.add_separator()
        if on_search:
            self._toolbar.add_search(placeholder=search_placeholder,
                                     on_change=on_search)
        else:
            self._toolbar.add_stretch()
        root.addWidget(self._toolbar)

        # ── Table ─────────────────────────────────────────
        self.table = QTableWidget()
        setup_table(self.table, columns)
        self.table.selectionModel().selectionChanged.connect(self._on_select)
        root.addWidget(self.table)

        # ── Empty state ───────────────────────────────────
        self._empty = EmptyState(t("empty.title"), t("empty.add_hint"))
        self._empty.setVisible(False)
        root.addWidget(self._empty)

        # ── Pagination ────────────────────────────────────
        self._pager: Pagination | None = None
        if on_page_change:
            self._pager = Pagination(total=0, page_size=page_size)
            self._pager.page_changed.connect(on_page_change)
            root.addWidget(self._pager)

        self._edit_label   = edit_label
        self._delete_label = delete_label

    # ── Public API ────────────────────────────────────────

    def load(self, data: list[dict], keys: list[str],
             id_key: str = "id", formatters: dict | None = None):
        """Load data vào table."""
        load_table(self.table, data, keys, id_key=id_key, formatters=formatters)
        has_data = len(data) > 0
        self.table.setVisible(has_data)
        self._empty.setVisible(not has_data)
        self._on_select()   # reset button state

    def set_total(self, total: int):
        """Cập nhật tổng số bản ghi cho pagination."""
        if self._pager:
            self._pager.set_total(total)

    def selected_id(self):
        """Lấy ID dòng đang chọn (UserRole cột 0). None nếu không chọn."""
        return get_selected_id(self.table)

    def clear_selection(self):
        self.table.clearSelection()
        self._on_select()

    def current_page(self) -> int:
        return self._pager.current_page() if self._pager else 1

    def offset(self) -> int:
        return self._pager.offset() if self._pager else 0

    def get_toolbar(self) -> ContentToolbar:
        return self._toolbar

    # ── Internal ──────────────────────────────────────────

    def _on_select(self):
        has = bool(self.table.selectionModel().selectedRows())
        self._toolbar.set_enabled(self._edit_label,   has)
        self._toolbar.set_enabled(self._delete_label, has)
        self.selection_changed.emit(has)
