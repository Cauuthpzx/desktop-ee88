"""
widgets/badge.py
Badge / Tag hiển thị trạng thái dạng label nhỏ.

Dùng:
    from widgets.badge import Badge, StatusBadge
    badge = Badge("Admin")
    badge = Badge("12")
    status = StatusBadge("active")   # "active" | "inactive" | "pending" | "error"
    layout.addWidget(badge)
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from core import theme


# Map trạng thái → text hiển thị
STATUS_TEXT = {
    "active":   "Hoạt động",
    "inactive": "Không hoạt động",
    "pending":  "Chờ xử lý",
    "error":    "Lỗi",
    "success":  "Thành công",
    "warning":  "Cảnh báo",
}


class Badge(QLabel):
    """
    Label nhỏ dạng badge — chỉ dùng border/padding mặc định của Qt.
    Không dùng stylesheet — dựa vào QFrame box để tạo viền.
    """
    def __init__(self, text: str):
        super().__init__(f" {text} ")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(theme.font(size=theme.FONT_SIZE_SM))
        self.setFrameShape(QLabel.Shape.Box)
        self.setFrameShadow(QLabel.Shadow.Plain)
        self.setLineWidth(1)


class StatusBadge(Badge):
    """
    Badge hiển thị trạng thái — text lấy từ STATUS_TEXT.
    status: "active" | "inactive" | "pending" | "error" | "success" | "warning"
    """
    def __init__(self, status: str):
        text = STATUS_TEXT.get(status, status)
        super().__init__(text)

    def set_status(self, status: str):
        text = STATUS_TEXT.get(status, status)
        self.setText(f" {text} ")
