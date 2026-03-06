"""
tabs/bet_lottery_tab.py — Tab Đơn cược xổ số
"""
from core.base_widgets import BaseTab, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud


COLUMNS = [
    "Nhân viên", "Mã giao dịch", "Tên người dùng",
    "Thời gian cược", "Trò chơi", "Loại trò chơi",
    "Cách chơi", "Kỳ", "Thông tin cược",
    "Tiền cược", "Tiền hoàn trả", "Thắng thua", "Trạng thái",
]
KEYS = [
    "staff", "transaction_code", "username",
    "bet_time", "game", "game_type",
    "play_method", "period", "bet_info",
    "bet_amount", "rebate", "win_loss", "status",
]


class BetLotteryTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("bet_lottery.title"), bold=True, size=theme.FONT_SIZE_LG)
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
            ("Trần Minh", "BL20260305001", "user001", "2026-03-05 14:30", "Mega 6/45", "Xổ số", "Chọn 6 số", "Kỳ 125", "01-12-23-34-40-45", 50_000, 0, -50_000, "Thua"),
            ("Lê Hương",  "BL20260304001", "user002", "2026-03-04 08:15", "Power 6/55", "Xổ số", "Chọn 6 số", "Kỳ 124", "05-10-20-30-40-55", 100_000, 5_000, 2_000_000, "Thắng"),
            ("Phạm Tuấn", "BL20260301001", "user003", "2026-03-01 19:00", "Max 3D",    "Xổ số", "Chọn 3 số", "Kỳ 123", "1-2-3",             20_000, 0, 0, "Đang chờ"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "transaction_code": row[1], "username": row[2],
                "bet_time": row[3], "game": row[4], "game_type": row[5],
                "play_method": row[6], "period": row[7], "bet_info": row[8],
                "bet_amount": row[9], "rebate": row[10], "win_loss": row[11],
                "status": row[12],
            })
            self._next_id += 1
        self._reload()

    def _reload(self, filter_text: str = ""):
        data = self._data
        if filter_text:
            q = filter_text.lower()
            data = [r for r in data
                    if q in r["username"].lower()
                    or q in r["staff"].lower()
                    or q in r["transaction_code"].lower()]
        self.crud.load(data, keys=KEYS)

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("bet_lottery.title"))
