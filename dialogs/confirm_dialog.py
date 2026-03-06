"""
dialogs/confirm_dialog.py
Các hàm dialog xác nhận / thông báo dùng chung toàn app.

Dùng:
    from dialogs.confirm_dialog import confirm, alert, warn, error
    if confirm(self, "Xoá bản ghi này?"): ...
    alert(self, "Lưu thành công!")
"""
from PyQt6.QtWidgets import QMessageBox, QWidget
from core.i18n import t


def confirm(parent: QWidget, message: str, title: str = "") -> bool:
    """Hỏi Yes/No — True nếu chọn Yes."""
    r = QMessageBox.question(
        parent, title or t("dialog.confirm"), message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    return r == QMessageBox.StandardButton.Yes


def confirm_delete(parent: QWidget, name: str = "") -> bool:
    """Shortcut xác nhận xoá."""
    display_name = name or t("empty.title")
    return confirm(
        parent,
        t("dialog.confirm_delete_msg", name=display_name),
        t("dialog.confirm_delete"),
    )


def alert(parent: QWidget, message: str, title: str = "") -> None:
    QMessageBox.information(parent, title or t("dialog.alert"), message)


def warn(parent: QWidget, message: str, title: str = "") -> None:
    QMessageBox.warning(parent, title or t("dialog.warning"), message)


def error(parent: QWidget, message: str, title: str = "") -> None:
    QMessageBox.critical(parent, title or t("dialog.error"), message)


def success(parent: QWidget, message: str) -> None:
    """Thông báo thành công."""
    QMessageBox.information(parent, t("dialog.success"), message)
