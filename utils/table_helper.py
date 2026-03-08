"""
utils/table_helper.py
Hàm tiện ích cho QTableWidget dùng chung.

Dùng:
    from utils.table_helper import (
        setup_table, load_table, get_selected_id,
        clear_selection, set_row_data
    )

    setup_table(self.table, ["ID", "Tên", "Tuổi"])
    load_table(self.table, data, keys=["id", "name", "age"])
    id_ = get_selected_id(self.table)   # lấy ID từ cột 0
"""
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QApplication
from PyQt6.QtCore import Qt
from widgets.notify import NotifyOverlay


def _get_copy_overlay(table: QTableWidget) -> NotifyOverlay:
    """Lấy hoặc tạo NotifyOverlay dành cho copy trên table viewport."""
    viewport = table.viewport()
    overlay = getattr(viewport, "_copy_overlay", None)
    if overlay is None:
        overlay = NotifyOverlay(viewport)
        viewport._copy_overlay = overlay  # type: ignore[attr-defined]
    return overlay


def _on_double_click(table: QTableWidget, index) -> None:
    """Copy cell value to clipboard on double-click."""
    item = table.item(index.row(), index.column())
    if item and item.text():
        QApplication.clipboard().setText(item.text())
        overlay = _get_copy_overlay(table)
        display = item.text()[:40]
        overlay.notify("success", f"Đã copy: {display}")


def setup_table(table: QTableWidget,
                headers: list[str],
                stretch_last: bool = True,
                row_height: int | None = None) -> None:
    """Cấu hình QTableWidget chuẩn."""
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)

    table.setMouseTracking(True)
    table.viewport().setMouseTracking(True)
    table.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
    table.horizontalHeader().setMouseTracking(True)
    table.horizontalHeader().setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    # Double-click cell → copy value
    table.doubleClicked.connect(lambda idx: _on_double_click(table, idx))

    if stretch_last:
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    else:
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)

    if row_height:
        table.verticalHeader().setDefaultSectionSize(row_height)


def load_table(table: QTableWidget,
               data: list[dict],
               keys: list[str],
               id_key: str = "id",
               formatters: dict | None = None) -> None:
    """
    Load data vào table.
    - keys: thứ tự cột tương ứng với key trong dict
    - formatters: dict {key: fn} để format giá trị trước khi hiển thị
    - id_key: key dùng để lưu ID vào UserRole của cột 0

    Ví dụ:
        load_table(table, data, ["id", "name", "age"],
                   formatters={"age": lambda v: f"{v} tuổi"})
    """
    fmts = formatters or {}
    row_count = len(data)
    col_count = len(keys)
    center = Qt.AlignmentFlag.AlignCenter
    user_role = Qt.ItemDataRole.UserRole

    # Suppress repaints during bulk load
    table.setUpdatesEnabled(False)
    table.setSortingEnabled(False)
    table.setRowCount(row_count)

    for row, rec in enumerate(data):
        for col in range(col_count):
            key = keys[col]
            val = rec.get(key, "")
            if key in fmts:
                display = fmts[key](val)
            else:
                display = str(val) if val is not None else ""

            item = QTableWidgetItem(display)
            item.setTextAlignment(center)

            if col == 0:
                item.setData(user_role, rec.get(id_key))

            table.setItem(row, col, item)

    table.setUpdatesEnabled(True)


def get_selected_id(table: QTableWidget, col: int = 0):
    """Lấy ID (UserRole) của dòng đang chọn. None nếu không chọn."""
    rows = table.selectionModel().selectedRows()
    if not rows:
        return None
    item = table.item(rows[0].row(), col)
    return item.data(Qt.ItemDataRole.UserRole) if item else None


def get_selected_row(table: QTableWidget) -> int | None:
    """Lấy chỉ số dòng đang chọn."""
    rows = table.selectionModel().selectedRows()
    return rows[0].row() if rows else None


def get_cell(table: QTableWidget, row: int, col: int) -> str:
    item = table.item(row, col)
    return item.text() if item else ""


def clear_selection(table: QTableWidget):
    table.clearSelection()


def set_column_width(table: QTableWidget,
                     widths: dict[int, int]) -> None:
    """Đặt độ rộng cột cụ thể, các cột còn lại stretch.
    widths: {col_index: width_px}
    """
    header = table.horizontalHeader()
    for col in range(table.columnCount()):
        if col in widths:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(col, widths[col])
        else:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
