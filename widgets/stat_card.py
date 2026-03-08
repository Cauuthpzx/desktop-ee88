"""
widgets/stat_card.py
Thẻ thống kê hiển thị tiêu đề + giá trị lớn.

Dùng:
    from widgets.stat_card import StatCard
    card = StatCard("Người dùng", "128")
    card = StatCard("Doanh thu", "9.200.000", suffix="đ")
    layout.addWidget(card)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from core import theme


class StatCard(QFrame):
    def __init__(self, title: str, value: str,
                 suffix: str = "",
                 min_width: int = 140,
                 value_size: int = theme.FONT_SIZE_XL):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setMinimumWidth(min_width)

        compact = value_size < theme.FONT_SIZE_XL
        pad_h = theme.SPACING_MD if compact else theme.SPACING_LG
        pad_v = theme.SPACING_SM if compact else theme.SPACING_MD

        lay = QVBoxLayout(self)
        lay.setContentsMargins(pad_h, pad_v, pad_h, pad_v)
        lay.setSpacing(theme.SPACING_XS if compact else theme.SPACING_SM)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setFont(theme.font(size=theme.FONT_SIZE_SM))

        display = f"{value}{suffix}"
        lbl_value = QLabel(display)
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_value.setFont(theme.font(size=value_size, bold=True))

        self._lbl_title = lbl_title
        self._lbl_value = lbl_value
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_value)

    def set_title(self, title: str) -> None:
        """Cập nhật tiêu đề thẻ."""
        self._lbl_title.setText(title)

    def update_value(self, value: str, suffix: str = "") -> None:
        """Cập nhật giá trị hiển thị."""
        self._lbl_value.setText(f"{value}{suffix}")

    def set_value_color(self, color: str) -> None:
        """Đặt màu cho giá trị (e.g. 'green', 'red', '')."""
        if color:
            self._lbl_value.setStyleSheet(f"color: {color};")
        else:
            self._lbl_value.setStyleSheet("")
