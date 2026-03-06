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


def get_text(parent: QWidget, label: str,
             title: str = "Nhập liệu",
             default: str = "") -> str | None:
    """Trả về chuỗi đã nhập, None nếu cancel."""
    text, ok = QInputDialog.getText(parent, title, label, text=default)
    return text.strip() if ok else None


def get_int(parent: QWidget, label: str,
            title: str = "Nhập số",
            default: int = 0,
            min_val: int = -999999,
            max_val: int = 999999) -> int | None:
    val, ok = QInputDialog.getInt(parent, title, label, default, min_val, max_val)
    return val if ok else None


def get_float(parent: QWidget, label: str,
              title: str = "Nhập số thực",
              default: float = 0.0,
              decimals: int = 2) -> float | None:
    val, ok = QInputDialog.getDouble(parent, title, label, default, decimals=decimals)
    return val if ok else None


def get_choice(parent: QWidget, label: str,
               choices: list[str],
               title: str = "Chọn",
               current: int = 0) -> str | None:
    item, ok = QInputDialog.getItem(parent, title, label, choices, current, False)
    return item if ok else None
