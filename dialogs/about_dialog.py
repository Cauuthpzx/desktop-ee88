"""
dialogs/about_dialog.py
Dialog "Về ứng dụng" dùng chung.

Dùng:
    from dialogs.about_dialog import AboutDialog
    dlg = AboutDialog(self)
    dlg.exec()

    # Hoặc tuỳ chỉnh thông tin:
    dlg = AboutDialog(self,
        app_name="Quản lý kho",
        version="1.0.0",
        description="Phần mềm quản lý kho hàng",
        author="Nguyen Van A",
        year="2026"
    )
    dlg.exec()
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from core.base_widgets import vbox, divider
from core import theme


class AboutDialog(QDialog):
    def __init__(self, parent=None,
                 app_name:    str = "My App",
                 version:     str = "1.0.0",
                 description: str = "",
                 author:      str = "",
                 year:        str = "2026"):
        super().__init__(parent)
        self.setWindowTitle(f"Về {app_name}")
        self.setMinimumWidth(320)
        self.setFixedHeight(220)

        root = vbox(margins=theme.MARGIN_DIALOG)
        self.setLayout(root)

        # App name
        lbl_name = QLabel(app_name)
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name.setFont(theme.font(size=theme.FONT_SIZE_XL, bold=True))
        root.addWidget(lbl_name)

        # Version
        lbl_ver = QLabel(f"Phiên bản {version}")
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ver.setFont(theme.font(size=theme.FONT_SIZE_SM))
        root.addWidget(lbl_ver)

        root.addWidget(divider())

        # Description
        if description:
            lbl_desc = QLabel(description)
            lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_desc.setWordWrap(True)
            lbl_desc.setFont(theme.font())
            root.addWidget(lbl_desc)

        # Author + year
        if author:
            lbl_author = QLabel(f"{author}  —  {year}")
            lbl_author.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_author.setFont(theme.font(size=theme.FONT_SIZE_SM))
            root.addWidget(lbl_author)

        root.addStretch()

        # Close button
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)
