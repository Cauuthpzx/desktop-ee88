"""
utils/export_table.py — Xuất dữ liệu QTableWidget hoặc raw data ra file Excel (.xlsx).

Dùng:
    from utils.export_table import export_table, export_data
    export_table(parent_widget, table_widget)
    export_data(parent_widget, headers, rows, keys, formatters, default_name)
"""
from __future__ import annotations

import logging

from PyQt6.QtWidgets import QTableWidget, QWidget

from core.i18n import t
from dialogs.file_dialog import save_file, EXCEL_FILES

logger = logging.getLogger(__name__)


def export_table(parent: QWidget, table: QTableWidget,
                 default_name: str = "export.xlsx") -> bool:
    """Xuất toàn bộ dữ liệu trong QTableWidget ra file Excel."""
    if table.rowCount() == 0:
        from dialogs.confirm_dialog import warn
        warn(parent, t("crud.export_empty"))
        return False

    path = save_file(parent, default_name=default_name, filters=EXCEL_FILES)
    if not path:
        return False

    if not path.lower().endswith(".xlsx"):
        path += ".xlsx"

    try:
        _write_xlsx_from_table(table, path)
        from dialogs.confirm_dialog import success
        success(parent, t("crud.export_success"))
        return True
    except Exception as e:
        logger.error("Export failed: %s", e, exc_info=True)
        from dialogs.confirm_dialog import error
        error(parent, t("crud.export_error"))
        return False


def export_data(parent: QWidget,
                headers: list[str],
                rows: list[dict],
                keys: list[str],
                formatters: dict | None = None,
                default_name: str = "export.xlsx") -> bool:
    """Xuất raw data (list[dict]) ra file Excel.

    Dùng khi cần xuất toàn bộ dữ liệu từ nhiều page,
    không chỉ dữ liệu hiện trên table.
    """
    if not rows:
        from dialogs.confirm_dialog import warn
        warn(parent, t("crud.export_empty"))
        return False

    path = save_file(parent, default_name=default_name, filters=EXCEL_FILES)
    if not path:
        return False

    if not path.lower().endswith(".xlsx"):
        path += ".xlsx"

    try:
        _write_xlsx_from_data(headers, rows, keys, formatters or {}, path)
        from dialogs.confirm_dialog import success
        success(parent, t("crud.export_success"))
        return True
    except Exception as e:
        logger.error("Export failed: %s", e, exc_info=True)
        from dialogs.confirm_dialog import error
        error(parent, t("crud.export_error"))
        return False


def _write_xlsx_from_table(table: QTableWidget, path: str) -> None:
    import xlsxwriter

    wb = xlsxwriter.Workbook(path)
    ws = wb.add_worksheet()

    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#4472C4", "font_color": "#FFFFFF",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    cell_fmt = wb.add_format({"border": 1, "align": "center", "valign": "vcenter"})

    col_count = table.columnCount()
    row_count = table.rowCount()

    for col in range(col_count):
        header_item = table.horizontalHeaderItem(col)
        ws.write(0, col, header_item.text() if header_item else f"Col {col}", header_fmt)

    for row in range(row_count):
        for col in range(col_count):
            item = table.item(row, col)
            ws.write(row + 1, col, item.text() if item else "", cell_fmt)

    # Auto-fit column widths
    for col in range(col_count):
        header_item = table.horizontalHeaderItem(col)
        max_len = len(header_item.text()) if header_item else 5
        for row in range(min(row_count, 100)):
            item = table.item(row, col)
            if item and item.text():
                max_len = max(max_len, len(item.text()))
        ws.set_column(col, col, min(max_len + 4, 50))

    wb.close()


def _write_xlsx_from_data(headers: list[str], rows: list[dict],
                          keys: list[str], formatters: dict,
                          path: str) -> None:
    import xlsxwriter

    wb = xlsxwriter.Workbook(path)
    ws = wb.add_worksheet()

    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#4472C4", "font_color": "#FFFFFF",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    cell_fmt = wb.add_format({"border": 1, "align": "center", "valign": "vcenter"})

    for col, h in enumerate(headers):
        ws.write(0, col, h, header_fmt)

    col_widths = [len(h) for h in headers]
    for r, rec in enumerate(rows):
        for c, key in enumerate(keys):
            val = rec.get(key, "")
            if key in formatters:
                display = formatters[key](val)
            else:
                display = str(val) if val is not None else ""
            ws.write(r + 1, c, display, cell_fmt)
            if r < 100:
                col_widths[c] = max(col_widths[c], len(display))

    for col, w in enumerate(col_widths):
        ws.set_column(col, col, min(w + 4, 50))

    wb.close()
