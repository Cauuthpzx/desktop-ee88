"""
home_tab.py — Tab trang chủ mẫu
"""
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from core.base_widgets import BaseTab, group, section_label, label, divider
from core import theme


class HomeTab(BaseTab):
    def _build(self, layout: QVBoxLayout):
        # Tiêu đề
        title = section_label("Trang chủ")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(divider())

        # Stat cards
        grp, g = group("Thống kê", layout_type="hbox")
        for title_text, value in [
            ("Người dùng", "128"),
            ("Đơn hàng",   "54"),
            ("Doanh thu",  "9.200"),
        ]:
            card = _StatCard(title_text, value)
            g.addWidget(card)
        g.addStretch()
        layout.addWidget(grp)

        # Thông báo
        grp2, g2 = group("Thông báo gần đây")
        for msg in [
            "Người dùng Alice vừa đăng nhập",
            "Đơn hàng #1042 đã được xác nhận",
            "Báo cáo tháng 3 đã sẵn sàng",
        ]:
            g2.addWidget(label(f"• {msg}"))
        layout.addWidget(grp2)

        layout.addStretch()


class _StatCard(QLabel):
    """Widget thẻ thống kê nhỏ."""
    def __init__(self, title: str, value: str):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(theme.SPACING_LG, theme.SPACING_MD,
                               theme.SPACING_LG, theme.SPACING_MD)
        lbl_title = label(title, size=theme.FONT_SIZE_SM)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_value = label(value, bold=True, size=theme.FONT_SIZE_XL)
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_value)
        self.setFrameShape(self.Shape.Box)
        self.setMinimumWidth(120)
