"""
widgets/breadcrumb.py
Đường dẫn điều hướng Breadcrumb.

Dùng:
    from widgets.breadcrumb import Breadcrumb
    bc = Breadcrumb(["Trang chủ", "Quản lý", "Chi tiết"])
    bc.item_clicked.connect(lambda index, text: print(index, text))
    layout.addWidget(bc)

    # Cập nhật đường dẫn:
    bc.set_path(["Trang chủ", "Báo cáo"])
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from core import theme


class Breadcrumb(QWidget):
    item_clicked = pyqtSignal(int, str)   # index, text

    def __init__(self, path: list[str] | None = None):
        super().__init__()
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(*theme.MARGIN_ZERO)
        self._lay.setSpacing(theme.SPACING_XS)
        self._lay.addStretch()

        if path:
            self.set_path(path)

    def set_path(self, path: list[str]):
        # Xoá widget cũ
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, text in enumerate(path):
            is_last = i == len(path) - 1

            if is_last:
                lbl = QLabel(text)
                lbl.setFont(theme.font(bold=True))
                self._lay.addWidget(lbl)
            else:
                btn = QPushButton(text)
                btn.setFlat(True)
                btn.setFont(theme.font())
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                idx = i
                btn.clicked.connect(lambda _, ix=idx, tx=text: self.item_clicked.emit(ix, tx))
                self._lay.addWidget(btn)

                sep = QLabel("›")
                sep.setFont(theme.font())
                self._lay.addWidget(sep)

        self._lay.addStretch()
