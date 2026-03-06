"""
dialogs/file_dialog.py
Wrapper QFileDialog dùng chung.

Dùng:
    from dialogs.file_dialog import open_file, save_file, open_folder
    path = open_file(self, filters="Excel (*.xlsx);;CSV (*.csv)")
    path = save_file(self, default_name="bao_cao.xlsx")
    folder = open_folder(self)
"""
from PyQt6.QtWidgets import QFileDialog, QWidget


ALL_FILES   = "Tất cả tệp (*)"
IMAGE_FILES = "Hình ảnh (*.png *.jpg *.jpeg *.bmp *.gif)"
EXCEL_FILES = "Excel (*.xlsx *.xls)"
CSV_FILES   = "CSV (*.csv)"
PDF_FILES   = "PDF (*.pdf)"
TEXT_FILES  = "Văn bản (*.txt)"


def open_file(parent: QWidget,
              title: str = "Mở tệp",
              start_dir: str = "",
              filters: str = ALL_FILES) -> str | None:
    """Chọn 1 file để mở. Trả về đường dẫn hoặc None."""
    path, _ = QFileDialog.getOpenFileName(parent, title, start_dir, filters)
    return path or None


def open_files(parent: QWidget,
               title: str = "Mở nhiều tệp",
               start_dir: str = "",
               filters: str = ALL_FILES) -> list[str]:
    """Chọn nhiều file. Trả về list đường dẫn."""
    paths, _ = QFileDialog.getOpenFileNames(parent, title, start_dir, filters)
    return paths


def save_file(parent: QWidget,
              title: str = "Lưu tệp",
              start_dir: str = "",
              default_name: str = "",
              filters: str = ALL_FILES) -> str | None:
    """Chọn nơi lưu file. Trả về đường dẫn hoặc None."""
    import os
    start = os.path.join(start_dir, default_name) if default_name else start_dir
    path, _ = QFileDialog.getSaveFileName(parent, title, start, filters)
    return path or None


def open_folder(parent: QWidget,
                title: str = "Chọn thư mục",
                start_dir: str = "") -> str | None:
    """Chọn thư mục. Trả về đường dẫn hoặc None."""
    path = QFileDialog.getExistingDirectory(parent, title, start_dir)
    return path or None
