"""
widgets/error_state.py
Hiển thị trang lỗi với hình ảnh SVG + tiêu đề + mô tả.

Dùng:
    from widgets.error_state import ErrorState

    err = ErrorState(code=401)
    layout.addWidget(err)

    # Hoặc tuỳ chỉnh:
    err = ErrorState(code=500, title="Lỗi máy chủ", description="Vui lòng thử lại sau.")
"""
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtSvg import QSvgRenderer
from core import theme
from core.i18n import t

_IMAGE_DIR = Path("image")

# Map HTTP error code → SVG file
_CODE_FILES = {
    401: "401.svg",
    403: "403.svg",
    404: "404.svg",
    500: "500.svg",
}


class ErrorState(QWidget):
    """Error state widget with SVG illustration + title + description + retry button."""

    def __init__(self, code: int = 500, title: str = "",
                 description: str = "", on_retry=None,
                 parent: QWidget | None = None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(theme.SPACING_MD)
        lay.setContentsMargins(*theme.MARGIN_DEFAULT)

        # SVG image
        svg_file = _IMAGE_DIR / _CODE_FILES.get(code, "500.svg")
        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if svg_file.exists():
            renderer = QSvgRenderer(str(svg_file))
            # Render at 260x200 for nice inline display
            pixmap = QPixmap(260, 200)
            pixmap.fill(Qt.GlobalColor.transparent)
            from PyQt6.QtGui import QPainter
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self._img_label.setPixmap(pixmap)
        lay.addWidget(self._img_label)

        # Title
        if not title:
            title = t(f"error_state.title_{code}", fallback=str(code))
        self._title_lbl = QLabel(title)
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setFont(theme.font(size=theme.FONT_SIZE_LG, bold=True))
        lay.addWidget(self._title_lbl)

        # Description
        if not description:
            description = t(f"error_state.desc_{code}", fallback="")
        if description:
            self._desc_lbl = QLabel(description)
            self._desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._desc_lbl.setFont(theme.font())
            self._desc_lbl.setWordWrap(True)
            lay.addWidget(self._desc_lbl)

        # Retry button
        if on_retry:
            self._retry_btn = QPushButton(t("error_state.retry"))
            self._retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._retry_btn.clicked.connect(on_retry)
            lay.addWidget(self._retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)
