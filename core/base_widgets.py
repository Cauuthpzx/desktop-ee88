"""
base_widgets.py — Base classes và factory functions dùng chung
Mọi widget trong dự án nên dùng các hàm này thay vì tạo trực tiếp
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QSizePolicy, QDialog,
    QDialogButtonBox, QSpinBox, QComboBox, QTextEdit,
    QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core import theme


# ═══════════════════════════════════════════════════════════
#  LAYOUT FACTORIES
# ═══════════════════════════════════════════════════════════

def vbox(spacing: int = theme.SPACING_MD,
         margins: tuple = theme.MARGIN_DEFAULT) -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setSpacing(spacing)
    lay.setContentsMargins(*margins)
    return lay


def hbox(spacing: int = theme.SPACING_MD,
         margins: tuple = theme.MARGIN_DEFAULT) -> QHBoxLayout:
    lay = QHBoxLayout()
    lay.setSpacing(spacing)
    lay.setContentsMargins(*margins)
    return lay


def form_layout(margins: tuple = theme.MARGIN_DEFAULT) -> QFormLayout:
    lay = QFormLayout()
    lay.setSpacing(theme.SPACING_MD)
    lay.setContentsMargins(*margins)
    lay.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    return lay


# ═══════════════════════════════════════════════════════════
#  WIDGET FACTORIES
# ═══════════════════════════════════════════════════════════

def label(text: str = "",
          bold: bool = False,
          size: int = theme.FONT_SIZE) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(theme.font(size=size, bold=bold))
    return lbl


def section_label(text: str) -> QLabel:
    """Label tiêu đề section — bold, size LG."""
    return label(text, bold=True, size=theme.FONT_SIZE_LG)


def group(title: str, layout_type: str = "vbox") -> tuple[QGroupBox, QVBoxLayout | QHBoxLayout | QFormLayout]:
    """Trả về (groupbox, layout) đã gắn sẵn."""
    grp = QGroupBox(title)
    if layout_type == "hbox":
        lay = hbox(margins=theme.MARGIN_DEFAULT)
    elif layout_type == "form":
        lay = form_layout()
    else:
        lay = vbox(margins=theme.MARGIN_DEFAULT)
    grp.setLayout(lay)
    return grp, lay


def divider(orientation: str = "h") -> QFrame:
    """Đường kẻ phân cách ngang hoặc dọc."""
    line = QFrame()
    if orientation == "h":
        line.setFrameShape(QFrame.Shape.HLine)
    else:
        line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


# ═══════════════════════════════════════════════════════════
#  SCROLL TAB — dùng để tạo nội dung tab có scroll
# ═══════════════════════════════════════════════════════════

def scroll_tab() -> tuple[QScrollArea, QVBoxLayout]:
    """
    Tạo QScrollArea phù hợp làm nội dung tab.
    Trả về (scroll_area, inner_layout) — addWidget vào inner_layout.
    """
    inner = QWidget()
    l, _t, r, b = theme.MARGIN_DEFAULT
    inner_lay = vbox(margins=(l, _t - 1, r, b), spacing=theme.SPACING_LG)
    inner_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
    inner.setLayout(inner_lay)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(inner)
    return scroll, inner_lay


# ═══════════════════════════════════════════════════════════
#  BASE TAB WIDGET
# ═══════════════════════════════════════════════════════════

class BaseTab(QWidget):
    """
    Base class cho mọi tab content.
    Tự động có scroll. Subclass override _build(layout).

    Cách dùng:
        class MyTab(BaseTab):
            def _build(self, layout):
                grp, g = group("My Group")
                g.addWidget(QLabel("Hello"))
                layout.addWidget(grp)
    """
    def __init__(self):
        super().__init__()
        root = vbox(margins=theme.MARGIN_ZERO, spacing=0)
        self.setLayout(root)

        scroll, self._layout = scroll_tab()
        root.addWidget(scroll)

        self._build(self._layout)

    def _build(self, layout: QVBoxLayout) -> None:
        """Override để thêm widget vào layout."""
        pass


# ═══════════════════════════════════════════════════════════
#  BASE DIALOG
# ═══════════════════════════════════════════════════════════

class BaseDialog(QDialog):
    """
    Base class cho mọi QDialog trong dự án.
    Có sẵn form layout + OK/Cancel buttons.

    Cách dùng:
        class MyDialog(BaseDialog):
            def _build_form(self, form):
                self.name = QLineEdit()
                form.addRow("Name:", self.name)

            def get_data(self):
                return {"name": self.name.text()}
    """
    def __init__(self, parent=None, title: str = "Dialog",
                 min_width: int = 380, data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(min_width)

        layout = vbox(margins=theme.MARGIN_DIALOG)
        self.setLayout(layout)

        self._form = form_layout(margins=theme.MARGIN_ZERO)
        layout.addLayout(self._form)

        self._build_form(self._form)

        if data:
            self._fill(data)

        layout.addWidget(divider())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_form(self, form: QFormLayout) -> None:
        """Override để thêm field vào form."""
        pass

    def _fill(self, data: dict) -> None:
        """Override để pre-fill dữ liệu khi edit."""
        pass

    def get_data(self) -> dict:
        """Override để trả về dữ liệu từ form."""
        return {}
