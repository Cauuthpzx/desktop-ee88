"""
tabs/deposit_tab.py — Tab Nạp tiền
"""
from core.base_widgets import BaseTab, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud


COLUMNS = [
    "Nhân viên", "Tên tài khoản", "Thuộc đại lý",
    "Số tiền", "Loại hình giao dịch", "Trạng thái giao dịch",
    "Thời gian",
]
KEYS = [
    "staff", "account_name", "agent",
    "amount", "transaction_type", "status",
    "time",
]


class DepositTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("deposit.title"), bold=True, size=theme.FONT_SIZE_LG)
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
            ("Trần Minh", "user001", "agent001", 50_000_000, "Chuyển khoản", "Thành công", "2026-03-05 14:30"),
            ("Lê Hương",  "user002", "agent002", 10_000_000, "Ví điện tử",   "Thành công", "2026-03-04 08:15"),
            ("Phạm Tuấn", "user003", "agent003", 1_000_000,  "Thẻ cào",      "Đang xử lý", "2026-03-01 19:00"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "account_name": row[1], "agent": row[2],
                "amount": row[3], "transaction_type": row[4],
                "status": row[5], "time": row[6],
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
        self._title_lbl.setText(t("deposit.title"))
