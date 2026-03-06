"""
tabs/referral_tab.py — Tab Danh sách mã giới thiệu
"""
from PyQt6.QtWidgets import QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDialog
from core.base_widgets import BaseTab, BaseDialog, label, divider
from core import theme
from core.i18n import t
from widgets.table_crud import TableCrud
from dialogs.confirm_dialog import confirm_delete, warn
from utils.validators import validate_all, required


COLUMNS = [
    "Nhân viên", "Mã giới thiệu", "Loại hình giới thiệu",
    "Tổng số đã ĐK", "SL người dùng đã ĐK", "Số người nạp tiền",
    "Nạp đầu trong ngày", "Nạp đầu trong ngày (số tiền)",
    "Ghi chú", "Thời gian thêm vào",
]
KEYS = [
    "staff", "referral_code", "referral_type",
    "total_registered", "user_registered", "depositors",
    "first_deposit_today", "first_deposit_amount",
    "note", "created_at",
]

REFERRAL_TYPES = ["CPA", "Revenue Share", "Hybrid"]


# ═══════════════════════════════════════════════════════════
#  DIALOG
# ═══════════════════════════════════════════════════════════

class ReferralDialog(BaseDialog):
    def __init__(self, parent=None, data: dict | None = None):
        super().__init__(parent, title=t("referral.dialog_title"),
                         min_width=420, data=data)

    def _build_form(self, form):
        self.staff_edit = QLineEdit()
        self.staff_edit.setPlaceholderText("Tên nhân viên")
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("VD: REF001")
        self.type_combo = QComboBox()
        self.type_combo.addItems(REFERRAL_TYPES)
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Ghi chú...")

        form.addRow(t("referral.staff"),         self.staff_edit)
        form.addRow(t("referral.code"),          self.code_edit)
        form.addRow(t("referral.referral_type"), self.type_combo)
        form.addRow(t("referral.note"),          self.note_edit)

    def _fill(self, data: dict):
        self.staff_edit.setText(data.get("staff", ""))
        self.code_edit.setText(data.get("referral_code", ""))
        self.type_combo.setCurrentText(data.get("referral_type", REFERRAL_TYPES[0]))
        self.note_edit.setText(data.get("note", ""))

    def get_data(self) -> dict:
        return {
            "staff":         self.staff_edit.text().strip(),
            "referral_code": self.code_edit.text().strip(),
            "referral_type": self.type_combo.currentText(),
            "note":          self.note_edit.text().strip(),
        }


# ═══════════════════════════════════════════════════════════
#  TAB
# ═══════════════════════════════════════════════════════════

class ReferralTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("referral.title"), bold=True, size=theme.FONT_SIZE_LG)
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
            ("Trần Minh", "REF001", "CPA",           150, 120, 45, 3, 1_500_000, "Chiến dịch tháng 3",  "2025-12-01 10:00"),
            ("Lê Hương",  "REF002", "Revenue Share",  80,  65,  20, 1, 500_000,   "Đối tác A",           "2026-01-15 14:30"),
            ("Phạm Tuấn", "REF003", "Hybrid",         30,  25,  8,  0, 0,         "",                    "2026-02-20 09:15"),
        ]:
            self._data.append({
                "id": self._next_id,
                "staff": row[0], "referral_code": row[1], "referral_type": row[2],
                "total_registered": row[3], "user_registered": row[4], "depositors": row[5],
                "first_deposit_today": row[6], "first_deposit_amount": row[7],
                "note": row[8], "created_at": row[9],
            })
            self._next_id += 1
        self._reload()

    # ── Helpers ───────────────────────────────────────────

    def _reload(self, filter_text: str = ""):
        data = self._data
        if filter_text:
            q = filter_text.lower()
            data = [r for r in data
                    if q in r["staff"].lower()
                    or q in r["referral_code"].lower()
                    or q in r["note"].lower()]
        self.crud.load(data, keys=KEYS)

    # ── Slots ─────────────────────────────────────────────

    def _on_add(self):
        dlg = ReferralDialog(self.window())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([
            required(t("referral.code"), data["referral_code"]),
        ])
        if errors:
            warn(self.window(), "\n".join(errors))
            return
        data.update({
            "total_registered": 0, "user_registered": 0, "depositors": 0,
            "first_deposit_today": 0, "first_deposit_amount": 0,
            "created_at": "",
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
        dlg = ReferralDialog(self.window(), data=rec)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([required(t("referral.code"), data["referral_code"])])
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
        if rec and confirm_delete(self.window(), f"'{rec['referral_code']}'"):
            self._data = [r for r in self._data if r["id"] != id_]
            self._reload()

    def _on_search(self, text: str):
        self._reload(filter_text=text)

    def retranslate(self) -> None:
        self._title_lbl.setText(t("referral.title"))
