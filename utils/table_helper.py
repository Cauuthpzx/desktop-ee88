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
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt


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
    table.setRowCount(0)
    fmts = formatters or {}

    for rec in data:
        row = table.rowCount()
        table.insertRow(row)

        for col, key in enumerate(keys):
            val = rec.get(key, "")
            if key in fmts:
                display = fmts[key](val)
            else:
                display = str(val) if val is not None else ""

            item = QTableWidgetItem(display)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Lưu ID vào cột 0
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, rec.get(id_key))

            table.setItem(row, col, item)


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
