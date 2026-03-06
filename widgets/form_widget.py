"""
widgets/form_widget.py
Form nhúng trực tiếp trong tab (không phải dialog).
Dùng khi muốn hiển thị form ngay trên giao diện, không popup.

Dùng:
    from widgets.form_widget import FormWidget
    from PyQt6.QtWidgets import QLineEdit, QSpinBox, QComboBox

    form = FormWidget(
        fields=[
            ("Tên",     QLineEdit()),
            ("Tuổi",    QSpinBox()),
            ("Vai trò", QComboBox()),
        ],
        title="Thông tin người dùng"
    )
    form.btn_save.clicked.connect(self._on_save)
    form.btn_cancel.clicked.connect(self._on_cancel)
    layout.addWidget(form)

    # Lấy dữ liệu:
    data = form.values()

    # Load dữ liệu để sửa:
    form.load({"Tên": "Alice", "Tuổi": 28, "Vai trò": "Admin"})

    # Reset form:
    form.reset()
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QDateEdit,
)
from PyQt6.QtCore import pyqtSignal, Qt
from core.base_widgets import vbox, hbox, form_layout, divider
from core import theme


class FormWidget(QWidget):
    saved    = pyqtSignal(dict)   # emit khi nhấn Save
    cancelled = pyqtSignal()      # emit khi nhấn Cancel

    def __init__(self,
                 fields: list[tuple[str, QWidget]],
                 title: str = "",
                 save_label: str = "Lưu",
                 cancel_label: str = "Huỷ",
                 show_cancel: bool = True):
        super().__init__()
        self._widgets: dict[str, QWidget] = {}

        root = vbox(margins=theme.MARGIN_ZERO)
        self.setLayout(root)

        # Optional group title
        if title:
            grp = QGroupBox(title)
            inner = vbox(margins=theme.MARGIN_DEFAULT)
            grp.setLayout(inner)
            root.addWidget(grp)
            container = inner
        else:
            container = root

        # Form fields
        form = form_layout(margins=theme.MARGIN_ZERO)
        for label, widget in fields:
            self._widgets[label] = widget
            form.addRow(f"{label}:", widget)
        container.addLayout(form)

        container.addWidget(divider())

        # Buttons
        btn_row = hbox(margins=theme.MARGIN_ZERO)
        btn_row.addStretch()

        self.btn_save = QPushButton(save_label)
        self.btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self.btn_save)

        if show_cancel:
            self.btn_cancel = QPushButton(cancel_label)
            self.btn_cancel.clicked.connect(self.cancelled)
            btn_row.addWidget(self.btn_cancel)

        container.addLayout(btn_row)

    def _on_save(self):
        self.saved.emit(self.values())

    def values(self) -> dict:
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

    def load(self, data: dict):
        """Pre-fill dữ liệu vào form."""
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

    def reset(self):
        """Xoá trắng toàn bộ field."""
        for widget in self._widgets.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            elif isinstance(widget, QTextEdit):
                widget.clear()

    def set_readonly(self, readonly: bool):
        """Khoá/mở toàn bộ form."""
        for widget in self._widgets.values():
            widget.setEnabled(not readonly)
        self.btn_save.setEnabled(not readonly)
