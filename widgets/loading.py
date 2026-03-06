"""
widgets/loading.py
Loading indicator dùng QProgressBar indeterminate.

Dùng:
    from widgets.loading import LoadingBar, LoadingOverlay

    # 1. Loading bar đơn giản (nhúng vào layout):
    bar = LoadingBar()
    layout.addWidget(bar)
    bar.start()
    bar.stop()

    # 2. Overlay che toàn bộ widget cha:
    overlay = LoadingOverlay(parent_widget)
    overlay.show()
    # sau khi xong:
    overlay.hide()
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QProgressBar, QLabel, QFrame,
)
from PyQt6.QtCore import Qt
from core import theme
from core.i18n import t


class LoadingBar(QWidget):
    """Progress bar indeterminate + label text."""
    def __init__(self, text: str = ""):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(*theme.MARGIN_ZERO)
        lay.setSpacing(theme.SPACING_SM)

        self._label = QLabel(text or t("loading.processing"))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(theme.font())

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)   # indeterminate
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)

        lay.addWidget(self._label)
        lay.addWidget(self._bar)
        self.hide()

    def start(self, text: str | None = None):
        if text:
            self._label.setText(text)
        self.show()

    def stop(self):
        self.hide()

    def set_text(self, text: str):
        self._label.setText(text)


class LoadingOverlay(QWidget):
    """Overlay mờ che phủ toàn bộ widget cha khi đang xử lý."""
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        frame.setFixedSize(280, 80)
        frame_lay = QVBoxLayout(frame)
        frame_lay.setContentsMargins(*[theme.SPACING_LG] * 4)
        frame_lay.setSpacing(theme.SPACING_SM)

        self._label = QLabel(t("loading.processing"))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(theme.font())

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        self._bar.setFixedWidth(240)

        frame_lay.addWidget(self._label)
        frame_lay.addWidget(self._bar)
        lay.addWidget(frame)

    def start(self, text: str = ""):
        self._label.setText(text or t("loading.processing"))
        self.resize(self.parent().size())
        self.show()
        self.raise_()

    def stop(self):
        self.hide()

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)
