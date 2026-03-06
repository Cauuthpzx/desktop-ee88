"""
tabs/example_tab.py — Tab CRUD mẫu chuẩn
Copy file này làm template khi tạo tab mới.

Pattern:
  - Dùng TableCrud thay vì tự lắp toolbar + table + pagination
  - Dùng confirm_delete() thay vì QMessageBox trực tiếp
  - Dùng validate_all() thay vì if/else tự viết
  - Dùng BaseDialog cho form
"""
from PyQt6.QtWidgets import QLineEdit, QSpinBox, QComboBox, QDialog
from core.base_widgets import BaseTab, BaseDialog, label, divider
from core import theme
from widgets.table_crud import TableCrud
from dialogs.confirm_dialog import confirm_delete, warn
from utils.validators import validate_all, required, positive


COLUMNS = ["ID", "Tên", "Tuổi", "Vai trò"]
ROLES   = ["Admin", "User", "Guest"]


# ═══════════════════════════════════════════════════════════
#  DIALOG — kế thừa BaseDialog, override 3 method
# ═══════════════════════════════════════════════════════════

class PersonDialog(BaseDialog):
    def __init__(self, parent=None, data: dict | None = None):
        super().__init__(parent, title="Thêm / Sửa người dùng",
                         min_width=360, data=data)

    def _build_form(self, form):
        self.name_edit  = QLineEdit()
        self.name_edit.setPlaceholderText("Nhập họ tên...")
        self.age_spin   = QSpinBox()
        self.age_spin.setRange(1, 120)
        self.role_combo = QComboBox()
        self.role_combo.addItems(ROLES)
        form.addRow("Tên:",     self.name_edit)
        form.addRow("Tuổi:",    self.age_spin)
        form.addRow("Vai trò:", self.role_combo)

    def _fill(self, data: dict):
        self.name_edit.setText(data.get("name", ""))
        self.age_spin.setValue(data.get("age", 1))
        self.role_combo.setCurrentText(data.get("role", ROLES[0]))

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "age":  self.age_spin.value(),
            "role": self.role_combo.currentText(),
        }


# ═══════════════════════════════════════════════════════════
#  TAB — kế thừa BaseTab, override _build(layout)
# ═══════════════════════════════════════════════════════════

class ExampleTab(BaseTab):
    def _build(self, layout):
        layout.addWidget(label("Quản lý người dùng", bold=True,
                               size=theme.FONT_SIZE_LG))
        layout.addWidget(divider())

        # TableCrud tích hợp sẵn: Toolbar + Search + Table + EmptyState
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
        for name, age, role in [
            ("Alice", 28, "Admin"),
            ("Bob",   34, "User"),
            ("Carol", 25, "Guest"),
        ]:
            self._data.append({"id": self._next_id, "name": name,
                                "age": age, "role": role})
            self._next_id += 1
        self._reload()

    # ── Helpers ───────────────────────────────────────────

    def _reload(self, filter_text: str = ""):
        data = self._data
        if filter_text:
            data = [r for r in data
                    if filter_text.lower() in r["name"].lower()]
        self.crud.load(data, keys=["id", "name", "age", "role"])

    # ── Slots ─────────────────────────────────────────────

    def _on_add(self):
        dlg = PersonDialog(self.window())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([
            required("Tên", data["name"]),
            positive("Tuổi", data["age"]),
        ])
        if errors:
            warn(self.window(), "\n".join(errors))
            return
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
        dlg = PersonDialog(self.window(), data=rec)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([required("Tên", data["name"])])
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
        if rec and confirm_delete(self.window(), f"'{rec['name']}'"):
            self._data = [r for r in self._data if r["id"] != id_]
            self._reload()

    def _on_search(self, text: str):
        self._reload(filter_text=text)
