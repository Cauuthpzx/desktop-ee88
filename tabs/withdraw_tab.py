"""
tabs/withdraw_tab.py — Tab Rút tiền
"""
from core.base_widgets import BaseTab, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud


COLUMNS = [
    "Nhân viên", "Mã giao dịch", "Thời gian tạo đơn",
    "Tên tài khoản", "Thuộc đại lý",
    "Số tiền yêu cầu", "Phí rút", "Số tiền thực nhận",
    "Trạng thái", "Thao tác",
]
KEYS = [
    "staff", "transaction_code", "created_time",
    "account_name", "agent",
    "requested_amount", "withdraw_fee", "actual_amount",
    "status", "action",
]


class WithdrawTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("withdraw.title"), bold=True, size=theme.FONT_SIZE_LG)
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
            ("Trần Minh", "WD20260305001", "2026-03-05 15:00", "user001", "agent001", 10_000_000, 50_000, 9_950_000, "Thành công", ""),
            ("Lê Hương",  "WD20260304001", "2026-03-04 09:30", "user002", "agent002", 2_000_000,  20_000, 1_980_000, "Thành công", ""),
            ("Phạm Tuấn", "WD20260301001", "2026-03-01 20:00", "user003", "agent003", 500_000,    5_000,  495_000,   "Đang xử lý", "Duyệt"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "transaction_code": row[1], "created_time": row[2],
                "account_name": row[3], "agent": row[4],
                "requested_amount": row[5], "withdraw_fee": row[6],
                "actual_amount": row[7], "status": row[8], "action": row[9],
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
                    or q in r["transaction_code"].lower()]
        self.crud.load(data, keys=KEYS)

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("withdraw.title"))
