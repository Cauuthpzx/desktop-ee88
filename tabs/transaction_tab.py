"""
tabs/transaction_tab.py — Tab Giao dịch (Sao kê)
"""
from core.base_widgets import BaseTab, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud


COLUMNS = [
    "Nhân viên", "Tên tài khoản", "Thuộc đại lý",
    "Số lần nạp", "Số tiền nạp", "Số lần rút", "Số tiền rút",
    "Phí dịch vụ", "Hoa hồng đại lý", "Ưu đãi",
    "Hoàn trả bên thứ 3", "Tiền thưởng bên thứ 3", "Thời gian",
]
KEYS = [
    "staff", "account_name", "agent",
    "deposit_count", "deposit_amount", "withdraw_count", "withdraw_amount",
    "service_fee", "agent_commission", "promotion",
    "third_party_rebate", "third_party_bonus", "time",
]


class TransactionTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("transaction.title"), bold=True, size=theme.FONT_SIZE_LG)
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
            ("Trần Minh", "user001", "agent001", 12, 50_000_000, 3, 8_000_000, 120_000, 500_000, 200_000, 150_000, 100_000, "2026-03-05 14:30"),
            ("Lê Hương",  "user002", "agent002", 5,  10_000_000, 1, 2_000_000, 30_000,  100_000, 50_000,  0,       0,       "2026-03-04 08:15"),
            ("Phạm Tuấn", "user003", "agent003", 1,  1_000_000,  0, 0,         0,       0,       0,       0,       0,       "2026-03-01 19:00"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "account_name": row[1], "agent": row[2],
                "deposit_count": row[3], "deposit_amount": row[4],
                "withdraw_count": row[5], "withdraw_amount": row[6],
                "service_fee": row[7], "agent_commission": row[8],
                "promotion": row[9], "third_party_rebate": row[10],
                "third_party_bonus": row[11], "time": row[12],
            })
            self._next_id += 1
        self._reload()

    def _reload(self, filter_text: str = ""):
        data = self._data
        if filter_text:
            q = filter_text.lower()
            data = [r for r in data
                    if q in r["account_name"].lower()
                    or q in r["staff"].lower()]
        self.crud.load(data, keys=KEYS)

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("transaction.title"))
