"""
home_tab.py — Tab trang chủ mẫu
"""
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt
from core.base_widgets import BaseTab, group, section_label, label, divider
from widgets.stat_card import StatCard


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
            g.addWidget(StatCard(title_text, value))
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
