"""
home_tab.py — Tab trang chủ mẫu
"""
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt
from core.base_widgets import BaseTab, group, section_label, label, divider
from core.i18n import t
from widgets.stat_card import StatCard


class HomeTab(BaseTab):
    def _build(self, layout: QVBoxLayout):
        self._title_lbl = section_label(t("home.title"))
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._title_lbl)
        layout.addWidget(divider())

        # Stat cards — store references for retranslate
        self._grp_stats, g = group(t("home.stats"), layout_type="hbox")
        self._stat_cards: list[tuple[StatCard, str]] = []  # (card, i18n_key)
        for key, value in [
            ("home.users",   "128"),
            ("home.orders",  "54"),
            ("home.revenue", "9.200"),
        ]:
            card = StatCard(t(key), value)
            self._stat_cards.append((card, key))
            g.addWidget(card)
        g.addStretch()
        layout.addWidget(self._grp_stats)

        # Thông báo
        self._grp_notif, g2 = group(t("home.notifications"))
        for msg in [
            "Người dùng Alice vừa đăng nhập",
            "Đơn hàng #1042 đã được xác nhận",
            "Báo cáo tháng 3 đã sẵn sàng",
        ]:
            g2.addWidget(label(f"• {msg}"))
        layout.addWidget(self._grp_notif)

        layout.addStretch()

    def retranslate(self) -> None:
        self._title_lbl.setText(t("home.title"))
        self._grp_stats.setTitle(t("home.stats"))
        self._grp_notif.setTitle(t("home.notifications"))
        for card, key in self._stat_cards:
            card.set_title(t(key))
