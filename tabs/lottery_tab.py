"""
tabs/lottery_tab.py — Tab Xổ số
"""
from core.base_widgets import BaseTab, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud


COLUMNS = [
    "Nhân viên", "Tên tài khoản", "Thuộc đại lý",
    "Số lần cược", "Tiền cược", "Tiền cược hợp lệ",
    "Hoàn trả", "Thắng thua", "KQ thắng thua", "Tiền trúng",
    "Tên loại xổ",
]
KEYS = [
    "staff", "account_name", "agent",
    "bet_count", "bet_amount", "valid_bet",
    "rebate", "win_loss", "net_win_loss", "prize",
    "lottery_type",
]


class LotteryTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("lottery.title"), bold=True, size=theme.FONT_SIZE_LG)
        layout.addWidget(self._title_lbl)
        layout.addWidget(divider())

        self.crud = TableCrud(
            columns=COLUMNS,
            on_search=self._on_search,
        )
        layout.addWidget(self.crud)

        self._next_id = 1
        self._data: list[dict] = []
        for row in [
            ("Trần Minh", "user001", "agent001", 120, 6_000_000, 5_500_000, 150_000, -800_000, -950_000, 5_200_000, "Mega 6/45"),
            ("Lê Hương",  "user002", "agent002", 45,  2_000_000, 1_800_000, 50_000,  300_000,  250_000,  2_300_000, "Power 6/55"),
            ("Phạm Tuấn", "user003", "agent003", 10,  500_000,   500_000,   0,       -500_000, -500_000, 0,          "Max 3D"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "account_name": row[1], "agent": row[2],
                "bet_count": row[3], "bet_amount": row[4], "valid_bet": row[5],
                "rebate": row[6], "win_loss": row[7], "net_win_loss": row[8],
                "prize": row[9], "lottery_type": row[10],
            })
            self._next_id += 1
        self._reload()

    def _reload(self, filter_text: str = ""):
        data = self._data
        if filter_text:
            q = filter_text.lower()
            data = [r for r in data
                    if q in r["account_name"].lower()
                    or q in r["staff"].lower()
                    or q in r["lottery_type"].lower()]
        self.crud.load(data, keys=KEYS)

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("lottery.title"))
