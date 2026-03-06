"""
dialogs/form_dialog.py
Form dialog linh hoạt dùng chung — truyền fields vào là dùng được.

Dùng:
    from dialogs.form_dialog import FormDialog
    from PyQt6.QtWidgets import QLineEdit, QSpinBox, QComboBox, QDialog

    dlg = FormDialog(
        parent=self,
        title="Thêm người dùng",
        fields=[
            ("Tên",     QLineEdit()),
            ("Tuổi",    QSpinBox()),
            ("Vai trò", QComboBox()),
        ]
    )
    if dlg.exec() == QDialog.DialogCode.Accepted:
        data = dlg.values()   # {"Tên": "Alice", "Tuổi": 28, ...}

    # Khi edit, truyền thêm data để pre-fill:
    dlg = FormDialog(self, "Sửa", fields=[...], data={"Tên": "Alice", "Tuổi": 28})
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QTextEdit, QCheckBox, QDateEdit, QWidget,
)
from PyQt6.QtCore import Qt, QDate
from core.base_widgets import vbox, form_layout, divider
from core import theme


class FormDialog(QDialog):
    def __init__(self, parent: QWidget | None = None,
                 title: str = "Form",
                 fields: list[tuple[str, QWidget]] | None = None,
                 data: dict | None = None,
                 min_width: int = 380):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(min_width)

        self._widgets: dict[str, QWidget] = {}

        root = vbox(margins=theme.MARGIN_DIALOG)
        self.setLayout(root)

        # Form
        form = form_layout(margins=theme.MARGIN_ZERO)
        for label, widget in (fields or []):
            self._widgets[label] = widget
            form.addRow(f"{label}:", widget)
        root.addLayout(form)

        # Pre-fill
        if data:
            self._fill(data)

        root.addWidget(divider())

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _fill(self, data: dict):
        for label, widget in self._widgets.items():
            val = data.get(label)
            if val is None:
                continue
            if isinstance(widget, QLineEdit):
                widget.setText(str(val))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(val)
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(val))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(val))
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(str(val))
            elif isinstance(widget, QDateEdit):
                if isinstance(val, QDate):
                    widget.setDate(val)

    def values(self) -> dict:
        """Trả về dict {label: value} từ tất cả field."""
        result = {}
        for label, widget in self._widgets.items():
            if isinstance(widget, QLineEdit):
                result[label] = widget.text().strip()
            elif isinstance(widget, QSpinBox):
                result[label] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                result[label] = widget.value()
            elif isinstance(widget, QComboBox):
                result[label] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                result[label] = widget.isChecked()
            elif isinstance(widget, QTextEdit):
                result[label] = widget.toPlainText().strip()
            elif isinstance(widget, QDateEdit):
                result[label] = widget.date().toString("yyyy-MM-dd")
        return result
