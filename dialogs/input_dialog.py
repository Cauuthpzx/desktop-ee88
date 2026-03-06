"""
dialogs/input_dialog.py
Wrapper QInputDialog dùng chung.

Dùng:
    from dialogs.input_dialog import get_text, get_int, get_choice
    name = get_text(self, "Nhập tên:")
    age  = get_int(self, "Nhập tuổi:", default=18)
    role = get_choice(self, "Chọn vai trò:", ["Admin", "User"])
"""
from PyQt6.QtWidgets import QInputDialog, QWidget
from core.i18n import t


def get_text(parent: QWidget, label: str,
             title: str = "",
             default: str = "") -> str | None:
    """Trả về chuỗi đã nhập, None nếu cancel."""
    text, ok = QInputDialog.getText(parent, title or t("dialog.input"), label, text=default)
    return text.strip() if ok else None


def get_int(parent: QWidget, label: str,
            title: str = "",
            default: int = 0,
            min_val: int = -999999,
            max_val: int = 999999) -> int | None:
    val, ok = QInputDialog.getInt(parent, title or t("dialog.input_number"), label, default, min_val, max_val)
    return val if ok else None


def get_float(parent: QWidget, label: str,
              title: str = "",
              default: float = 0.0,
              decimals: int = 2) -> float | None:
    val, ok = QInputDialog.getDouble(parent, title or t("dialog.input_float"), label, default, decimals=decimals)
    return val if ok else None


def get_choice(parent: QWidget, label: str,
               choices: list[str],
               title: str = "",
               current: int = 0) -> str | None:
    item, ok = QInputDialog.getItem(parent, title or t("dialog.choose"), label, choices, current, False)
    return item if ok else None
