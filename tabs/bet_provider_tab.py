"""
tabs/bet_provider_tab.py — Tab Đơn cược nhà cung cấp
"""
from core.base_widgets import BaseTab, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud


COLUMNS = [
    "Nhân viên", "Mã giao dịch", "Nhà cung cấp game bên thứ 3",
    "Tên tài khoản thuộc nhà cái", "Loại hình trò chơi",
    "Tên trò chơi bên thứ 3", "Tiền cược", "Tiền cược hợp lệ",
    "Tiền thưởng", "Thắng/Thua", "Thời gian cược",
]
KEYS = [
    "staff", "transaction_code", "third_party_provider",
    "house_account", "game_type",
    "third_party_game", "bet_amount", "valid_bet",
    "bonus", "win_loss", "bet_time",
]


class BetProviderTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("bet_provider.title"), bold=True, size=theme.FONT_SIZE_LG)
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
            ("Trần Minh", "BP20260305001", "Evolution Gaming", "user001", "Live Casino", "Lightning Roulette", 10_000_000, 9_500_000, 8_200_000, -1_800_000, "2026-03-05 14:30"),
            ("Lê Hương",  "BP20260304001", "Pragmatic Play",   "user002", "Slot Game",   "Sweet Bonanza",      4_000_000,  3_800_000, 4_500_000, 500_000,    "2026-03-04 08:15"),
            ("Phạm Tuấn", "BP20260301001", "Microgaming",      "user003", "Table Game",  "Blackjack Classic",  750_000,    750_000,   200_000,   -550_000,   "2026-03-01 19:00"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "transaction_code": row[1],
                "third_party_provider": row[2], "house_account": row[3],
                "game_type": row[4], "third_party_game": row[5],
                "bet_amount": row[6], "valid_bet": row[7],
                "bonus": row[8], "win_loss": row[9], "bet_time": row[10],
            })
            self._next_id += 1
        self._reload()

    def _reload(self, filter_text: str = ""):
        data = self._data
        if filter_text:
            q = filter_text.lower()
            data = [r for r in data
                    if q in r["house_account"].lower()
                    or q in r["staff"].lower()
                    or q in r["third_party_provider"].lower()]
        self.crud.load(data, keys=KEYS)

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("bet_provider.title"))
