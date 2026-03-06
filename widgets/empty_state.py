"""
widgets/empty_state.py
Hiển thị khi không có dữ liệu.

Dùng:
    from widgets.empty_state import EmptyState
    empty = EmptyState("Không có dữ liệu", "Thêm bản ghi mới để bắt đầu")
    layout.addWidget(empty)

    # Ẩn/hiện tuỳ theo có data không:
    empty.setVisible(len(data) == 0)
    table.setVisible(len(data) > 0)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from core import theme


class EmptyState(QWidget):
    def __init__(self, title: str = "Không có dữ liệu",
                 description: str = ""):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(theme.SPACING_SM)

        icon_lbl = QLabel("○")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFont(theme.font(size=32))
        lay.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setFont(theme.font(size=theme.FONT_SIZE_LG, bold=True))
        lay.addWidget(title_lbl)

        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
            desc_lbl.setWordWrap(True)
            lay.addWidget(desc_lbl)
