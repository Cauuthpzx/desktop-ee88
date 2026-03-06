"""
tabs/customer_tab.py — Tab Quản lý khách hàng
"""
from PyQt6.QtWidgets import QLineEdit, QComboBox, QDoubleSpinBox, QDialog
from core.base_widgets import BaseTab, BaseDialog, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud
from dialogs.confirm_dialog import confirm_delete, warn
from utils.validators import validate_all, required
from utils.formatters import currency


COLUMNS = [
    "Nhân viên", "Hội viên", "Loại hình hội viên",
    "Tài khoản đại lý", "Số dư", "Lần nạp", "Lần rút",
    "Tổng tiền nạp", "Tổng tiền rút",
    "TG đăng nhập cuối", "TG đăng ký", "Trạng thái",
]
KEYS = [
    "staff", "member", "member_type",
    "agent_account", "balance", "deposit_count", "withdraw_count",
    "total_deposit", "total_withdraw",
    "last_login", "registered_at", "status",
]

MEMBER_TYPES = ["VIP", "Gold", "Silver", "Standard"]
STATUSES = ["Hoạt động", "Khoá", "Chờ duyệt"]


# ═══════════════════════════════════════════════════════════
#  DIALOG
# ═══════════════════════════════════════════════════════════

class CustomerDialog(BaseDialog):
    def __init__(self, parent=None, data: dict | None = None):
        super().__init__(parent, title=t("customer.dialog_title"),
                         min_width=420, data=data)

    def _build_form(self, form):
        self.staff_edit = QLineEdit()
        self.staff_edit.setPlaceholderText("Tên nhân viên phụ trách")
        self.member_edit = QLineEdit()
        self.member_edit.setPlaceholderText("Tên hội viên")
        self.member_type_combo = QComboBox()
        self.member_type_combo.addItems(MEMBER_TYPES)
        self.agent_edit = QLineEdit()
        self.agent_edit.setPlaceholderText("Tài khoản đại lý")
        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setRange(0, 999_999_999)
        self.balance_spin.setDecimals(0)
        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUSES)

        form.addRow(t("customer.staff"),       self.staff_edit)
        form.addRow(t("customer.member"),      self.member_edit)
        form.addRow(t("customer.member_type"), self.member_type_combo)
        form.addRow(t("customer.agent"),       self.agent_edit)
        form.addRow(t("customer.balance"),     self.balance_spin)
        form.addRow(t("customer.status"),      self.status_combo)

    def _fill(self, data: dict):
        self.staff_edit.setText(data.get("staff", ""))
        self.member_edit.setText(data.get("member", ""))
        self.member_type_combo.setCurrentText(data.get("member_type", MEMBER_TYPES[0]))
        self.agent_edit.setText(data.get("agent_account", ""))
        self.balance_spin.setValue(data.get("balance", 0))
        self.status_combo.setCurrentText(data.get("status", STATUSES[0]))

    def get_data(self) -> dict:
        return {
            "staff":        self.staff_edit.text().strip(),
            "member":       self.member_edit.text().strip(),
            "member_type":  self.member_type_combo.currentText(),
            "agent_account": self.agent_edit.text().strip(),
            "balance":      int(self.balance_spin.value()),
            "status":       self.status_combo.currentText(),
        }


# ═══════════════════════════════════════════════════════════
#  TAB
# ═══════════════════════════════════════════════════════════

class CustomerTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("customer.title"), bold=True, size=theme.FONT_SIZE_LG)
        layout.addWidget(self._title_lbl)
        layout.addWidget(divider())

        self.crud = TableCrud(
            columns=COLUMNS,
            on_add=self._on_add,
            on_edit=self._on_edit,
            on_delete=self._on_delete,
            on_search=self._on_search,
        )
        layout.addWidget(self.crud)

        # Seed data mẫu
        self._next_id = 1
        self._data: list[dict] = []
        for row in [
            ("Trần Minh",  "Nguyễn Văn A", "VIP",      "agent001", 5_000_000, 12, 3, 50_000_000, 8_000_000,  "2026-03-05 14:30", "2025-01-10 09:00", "Hoạt động"),
            ("Lê Hương",   "Trần Thị B",   "Gold",     "agent002", 1_200_000, 5,  1, 10_000_000, 2_000_000,  "2026-03-04 08:15", "2025-06-20 11:30", "Hoạt động"),
            ("Phạm Tuấn",  "Lê Văn C",     "Standard", "agent003", 0,         0,  0, 0,          0,           "2026-03-01 19:00", "2026-02-28 16:45", "Chờ duyệt"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "member": row[1], "member_type": row[2],
                "agent_account": row[3], "balance": row[4],
                "deposit_count": row[5], "withdraw_count": row[6],
                "total_deposit": row[7], "total_withdraw": row[8],
                "last_login": row[9], "registered_at": row[10], "status": row[11],
            })
            self._next_id += 1
        self._reload()

    # ── Helpers ───────────────────────────────────────────

    def _reload(self, filter_text: str = ""):
        data = self._data
        if filter_text:
            q = filter_text.lower()
            data = [r for r in data
                    if q in r["member"].lower()
                    or q in r["staff"].lower()
                    or q in r["agent_account"].lower()]
        self.crud.load(data, keys=KEYS)

    # ── Slots ─────────────────────────────────────────────

    def _on_add(self):
        dlg = CustomerDialog(self.window())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([
            required(t("customer.member"), data["member"]),
        ])
        if errors:
            warn(self.window(), "\n".join(errors))
            return
        data.update({
            "deposit_count": 0, "withdraw_count": 0,
            "total_deposit": 0, "total_withdraw": 0,
            "last_login": "", "registered_at": "",
        })
        self._data.append({"id": self._next_id, **data})
        self._next_id += 1
        self._reload()

    def _on_edit(self):
        id_ = self.crud.selected_id()
        if id_ is None:
            return
        rec = next((r for r in self._data if r["id"] == id_), None)
        if rec is None:
            return
        dlg = CustomerDialog(self.window(), data=rec)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([required(t("customer.member"), data["member"])])
        if errors:
            warn(self.window(), "\n".join(errors))
            return
        rec.update(data)
        self._reload()

    def _on_delete(self):
        id_ = self.crud.selected_id()
        if id_ is None:
            return
        rec = next((r for r in self._data if r["id"] == id_), None)
        if rec and confirm_delete(self.window(), f"'{rec['member']}'"):
            self._data = [r for r in self._data if r["id"] != id_]
            self._reload()

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("customer.title"))
