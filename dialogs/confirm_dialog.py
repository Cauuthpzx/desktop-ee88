"""
dialogs/confirm_dialog.py
Các hàm dialog xác nhận / thông báo dùng chung toàn app.

Dùng:
    from dialogs.confirm_dialog import confirm, alert, warn, error
    if confirm(self, "Xoá bản ghi này?"): ...
    alert(self, "Lưu thành công!")
"""
from PyQt6.QtWidgets import QMessageBox, QWidget


def confirm(parent: QWidget, message: str, title: str = "Xác nhận") -> bool:
    """Hỏi Yes/No — True nếu chọn Yes."""
    r = QMessageBox.question(
        parent, title, message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    return r == QMessageBox.StandardButton.Yes


def confirm_delete(parent: QWidget, name: str = "bản ghi này") -> bool:
    """Shortcut xác nhận xoá."""
    return confirm(parent, f"Bạn có chắc muốn xoá {name}?", "Xác nhận xoá")


def alert(parent: QWidget, message: str, title: str = "Thông báo") -> None:
    QMessageBox.information(parent, title, message)


def warn(parent: QWidget, message: str, title: str = "Cảnh báo") -> None:
    QMessageBox.warning(parent, title, message)


def error(parent: QWidget, message: str, title: str = "Lỗi") -> None:
    QMessageBox.critical(parent, title, message)


def success(parent: QWidget, message: str) -> None:
    """Thông báo thành công."""
    QMessageBox.information(parent, "Thành công", message)
