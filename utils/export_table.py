"""
utils/export_table.py — Xuất dữ liệu QTableWidget ra file Excel (.xlsx).

Dùng:
    from utils.export_table import export_table
    export_table(parent_widget, table_widget)
"""
from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtWidgets import QTableWidget, QWidget

from core.i18n import t
from dialogs.file_dialog import save_file, EXCEL_FILES

logger = logging.getLogger(__name__)


def export_table(parent: QWidget, table: QTableWidget,
                 default_name: str = "export.xlsx") -> bool:
    """Xuất toàn bộ dữ liệu trong QTableWidget ra file Excel.

    Returns True nếu xuất thành công, False nếu huỷ hoặc lỗi.
    """
    if table.rowCount() == 0:
        from dialogs.confirm_dialog import warn
        warn(parent, t("crud.export_empty") if _has_key("crud.export_empty") else "Không có dữ liệu để xuất.")
        return False

    path = save_file(parent, default_name=default_name, filters=EXCEL_FILES)
    if not path:
        return False

    if not path.lower().endswith(".xlsx"):
        path += ".xlsx"

    try:
        _write_xlsx(table, path)
        from dialogs.confirm_dialog import success
        success(parent, t("crud.export_success") if _has_key("crud.export_success") else f"Đã xuất file:\n{path}")
        return True
    except Exception as e:
        logger.error("Export failed: %s", e, exc_info=True)
        from dialogs.confirm_dialog import error
        error(parent, t("crud.export_error") if _has_key("crud.export_error") else f"Không thể xuất file: {e}")
        return False


def _write_xlsx(table: QTableWidget, path: str) -> None:
    import xlsxwriter

    wb = xlsxwriter.Workbook(path)
    ws = wb.add_worksheet()

    # Header format
    header_fmt = wb.add_format({
        "bold": True,
        "bg_color": "#4472C4",
        "font_color": "#FFFFFF",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
    })

    col_count = table.columnCount()
    row_count = table.rowCount()

    # Write headers
    for col in range(col_count):
        header_item = table.horizontalHeaderItem(col)
        header_text = header_item.text() if header_item else f"Col {col}"
        ws.write(0, col, header_text, header_fmt)

    # Cell format
    cell_fmt = wb.add_format({"border": 1, "align": "center", "valign": "vcenter"})

    # Write data
    for row in range(row_count):
        for col in range(col_count):
            item = table.item(row, col)
            text = item.text() if item else ""
            ws.write(row + 1, col, text, cell_fmt)

    # Auto-fit column widths (approximate)
    for col in range(col_count):
        header_item = table.horizontalHeaderItem(col)
        max_len = len(header_item.text()) if header_item else 5
        for row in range(min(row_count, 100)):
            item = table.item(row, col)
            if item and item.text():
                max_len = max(max_len, len(item.text()))
        ws.set_column(col, col, min(max_len + 4, 50))

    wb.close()


def _has_key(key: str) -> bool:
    """Check if i18n key exists (avoid KeyError)."""
    val = t(key)
    return val != key
