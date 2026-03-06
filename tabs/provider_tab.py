"""
tabs/provider_tab.py — Tab Nhà cung cấp
"""
from core.base_widgets import BaseTab, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud


COLUMNS = [
    "Nhân viên", "Tên tài khoản", "Nhà cung cấp game",
    "Số lần cược", "Tiền cược", "Tiền cược hợp lệ",
    "Tiền thưởng", "Thắng thua",
]
KEYS = [
    "staff", "account_name", "provider",
    "bet_count", "bet_amount", "valid_bet",
    "bonus", "win_loss",
]


class ProviderTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("provider.title"), bold=True, size=theme.FONT_SIZE_LG)
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
            ("Trần Minh", "user001", "Evolution Gaming", 200, 10_000_000, 9_500_000, 8_200_000, -1_800_000),
            ("Lê Hương",  "user002", "Pragmatic Play",   80,  4_000_000,  3_800_000, 4_500_000, 500_000),
            ("Phạm Tuấn", "user003", "Microgaming",      15,  750_000,    750_000,   200_000,   -550_000),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "account_name": row[1], "provider": row[2],
                "bet_count": row[3], "bet_amount": row[4], "valid_bet": row[5],
                "bonus": row[6], "win_loss": row[7],
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
                    or q in r["provider"].lower()]
        self.crud.load(data, keys=KEYS)

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("provider.title"))
