"""
dialogs/login_window.py — Login / Register window (split layout).

Hiển thị trước AppWindow. Đăng nhập thành công emit signal `login_success`.
Nền: login-bg.svg. Card trắng nổi ở giữa, chia đôi branding | form.
"""
from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLineEdit, QCheckBox, QPushButton, QLabel, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QIcon, QFont, QPainter, QColor, QPalette, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from core import theme
from core.base_widgets import vbox, hbox, label, divider
from utils.validators import required, min_length, validate_all
from utils.settings import settings

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_ICON_AREA_W = 38


def _icon_path(name: str) -> str:
    return os.path.join(_BASE_DIR, "icons", "layui", name)


# ═══════════════════════════════════════════════════════════════════════════════
#  Icon Input — icon trái (nền riêng) + eye toggle NẰM TRONG input
# ═══════════════════════════════════════════════════════════════════════════════

class _IconInput(QWidget):
    """QLineEdit có icon bên trái (nền riêng). Eye toggle nằm bên trong edit."""

    def __init__(self, icon_svg: str, placeholder: str = "",
                 echo: QLineEdit.EchoMode = QLineEdit.EchoMode.Normal,
                 parent: QWidget | None = None):
        super().__init__(parent)
        lay = hbox(spacing=0, margins=theme.MARGIN_ZERO)
        self.setLayout(lay)

        # Icon area — nền nhạt
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedWidth(_ICON_AREA_W)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet(
            "background: palette(midlight);"
            "border: 1px solid palette(mid);"
            "border-right: none;"
            "border-top-left-radius: 3px;"
            "border-bottom-left-radius: 3px;"
            "padding: 4px;"
        )
        px = QIcon(icon_svg).pixmap(QSize(16, 16))
        if not px.isNull():
            self._icon_lbl.setPixmap(px)
        lay.addWidget(self._icon_lbl)

        # Input field
        self._is_password = (echo == QLineEdit.EchoMode.Password)
        right_pad = "30px" if self._is_password else "8px"
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setEchoMode(echo)
        self.edit.setStyleSheet(
            "border: 1px solid palette(mid);"
            "border-left: none;"
            "border-top-right-radius: 3px;"
            "border-bottom-right-radius: 3px;"
            f"padding: 4px {right_pad} 4px 8px;"
        )
        lay.addWidget(self.edit, 1)

        # Eye toggle — nằm BÊN TRONG edit (overlay)
        self._eye_btn: QPushButton | None = None
        if self._is_password:
            self._eye_btn = QPushButton(self.edit)
            self._eye_btn.setFlat(True)
            self._eye_btn.setFixedSize(26, 26)
            self._eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._eye_btn.setStyleSheet("background: transparent; border: none;")
            self._eye_icon = QIcon(_icon_path("eye.svg"))
            self._eye_off_icon = QIcon(_icon_path("eye-invisible.svg"))
            self._eye_btn.setIcon(self._eye_off_icon)
            self._eye_btn.setIconSize(QSize(14, 14))
            self._eye_btn.clicked.connect(self._toggle_visibility)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._eye_btn:
            y = (self.edit.height() - self._eye_btn.height()) // 2
            self._eye_btn.move(self.edit.width() - self._eye_btn.width() - 4, y)

    def _toggle_visibility(self) -> None:
        if self.edit.echoMode() == QLineEdit.EchoMode.Password:
            self.edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._eye_btn.setIcon(self._eye_icon)
        else:
            self.edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._eye_btn.setIcon(self._eye_off_icon)

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, text: str) -> None:
        self.edit.setText(text)

    def setFocus(self) -> None:
        self.edit.setFocus()

    def clear(self) -> None:
        self.edit.clear()


# ═══════════════════════════════════════════════════════════════════════════════
#  Branding Panel (bên trái)
# ═══════════════════════════════════════════════════════════════════════════════

class _BrandingPanel(QWidget):
    """Panel branding bên trái — logo + tên app + mô tả."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        lay = vbox(spacing=theme.SPACING_XL, margins=(32, 0, 32, 0))
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(lay)

        # Logo
        icon_path = os.path.join(_BASE_DIR, "icons", "app", "icon-titlebar.svg")
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico = QIcon(icon_path)
        if not ico.isNull():
            logo_label.setPixmap(ico.pixmap(QSize(64, 64)))
        lay.addWidget(logo_label)

        # App name
        app_name = label("My App", bold=True, size=theme.FONT_SIZE_XL + 2)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(app_name)

        # Description
        desc = label("PyQt6 Desktop Application", size=theme.FONT_SIZE)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        lay.addWidget(desc)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        accent = self.palette().highlight().color()
        bg = QColor(accent)
        bg.setAlpha(20)
        p.fillRect(self.rect(), bg)
        p.setPen(QColor(accent))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
#  Login Form
# ═══════════════════════════════════════════════════════════════════════════════

class _LoginForm(QWidget):
    login_requested = pyqtSignal(str, str, bool)   # username, password, remember
    cancel_requested = pyqtSignal()
    switch_to_register = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        lay = vbox(spacing=theme.SPACING_MD, margins=(28, 0, 28, 0))
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(lay)

        # Title
        title = label("ĐĂNG NHẬP", bold=True, size=theme.FONT_SIZE_LG)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        lay.addWidget(divider())

        # Username
        self._username = _IconInput(_icon_path("username.svg"), "Tên đăng nhập")
        lay.addWidget(self._username)

        # Password
        self._password = _IconInput(
            _icon_path("password.svg"), "Mật khẩu",
            echo=QLineEdit.EchoMode.Password,
        )
        lay.addWidget(self._password)

        # Remember me
        self._remember = QCheckBox("Nhớ đăng nhập")
        lay.addWidget(self._remember)

        # Error label
        self._error_lbl = QLabel()
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet("color: red;")
        self._error_lbl.hide()
        lay.addWidget(self._error_lbl)

        # Buttons: Đăng nhập + Huỷ (cùng độ rộng)
        btn_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        btn_login = QPushButton("Đăng nhập")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self._on_login)
        btn_cancel = QPushButton("Huỷ")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.cancel_requested.emit)
        btn_login.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_cancel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_lay.addWidget(btn_login)
        btn_lay.addWidget(btn_cancel)
        lay.addLayout(btn_lay)

        # Switch link
        switch_lay = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
        switch_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch_lay.addWidget(label("Chưa có tài khoản?"))
        link = QPushButton("Đăng ký")
        link.setFlat(True)
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.setStyleSheet("color: palette(highlight); text-decoration: underline;")
        link.clicked.connect(self.switch_to_register.emit)
        switch_lay.addWidget(link)
        lay.addLayout(switch_lay)

    def _on_login(self) -> None:
        username = self._username.text()
        password = self._password.text()

        errors = validate_all([
            required("Tên đăng nhập", username),
            required("Mật khẩu", password),
        ])
        if errors:
            self._show_error("\n".join(errors))
            return

        self._error_lbl.hide()
        self.login_requested.emit(username, password, self._remember.isChecked())

    def _show_error(self, msg: str) -> None:
        self._error_lbl.setText(msg)
        self._error_lbl.show()

    def load_remembered(self) -> None:
        if settings.get_bool("login/remember"):
            self._username.setText(settings.get_str("login/username"))
            self._remember.setChecked(True)
            self._password.setFocus()


# ═══════════════════════════════════════════════════════════════════════════════
#  Register Form
# ═══════════════════════════════════════════════════════════════════════════════

class _RegisterForm(QWidget):
    register_requested = pyqtSignal(str, str)  # username, password
    cancel_requested = pyqtSignal()
    switch_to_login = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        lay = vbox(spacing=theme.SPACING_MD, margins=(28, 0, 28, 0))
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(lay)

        # Title
        title = label("ĐĂNG KÝ", bold=True, size=theme.FONT_SIZE_LG)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        lay.addWidget(divider())

        # Username
        self._username = _IconInput(_icon_path("username.svg"), "Tên đăng nhập")
        lay.addWidget(self._username)

        # Password
        self._password = _IconInput(
            _icon_path("password.svg"), "Mật khẩu",
            echo=QLineEdit.EchoMode.Password,
        )
        lay.addWidget(self._password)

        # Confirm password
        self._confirm = _IconInput(
            _icon_path("password.svg"), "Xác nhận mật khẩu",
            echo=QLineEdit.EchoMode.Password,
        )
        lay.addWidget(self._confirm)

        # Error label
        self._error_lbl = QLabel()
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet("color: red;")
        self._error_lbl.hide()
        lay.addWidget(self._error_lbl)

        # Buttons: Đăng ký + Huỷ (cùng độ rộng)
        btn_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        btn_register = QPushButton("Đăng ký")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.clicked.connect(self._on_register)
        btn_cancel = QPushButton("Huỷ")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.cancel_requested.emit)
        btn_register.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_cancel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_lay.addWidget(btn_register)
        btn_lay.addWidget(btn_cancel)
        lay.addLayout(btn_lay)

        # Switch link
        switch_lay = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
        switch_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch_lay.addWidget(label("Đã có tài khoản?"))
        link = QPushButton("Đăng nhập")
        link.setFlat(True)
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.setStyleSheet("color: palette(highlight); text-decoration: underline;")
        link.clicked.connect(self.switch_to_login.emit)
        switch_lay.addWidget(link)
        lay.addLayout(switch_lay)

    def _on_register(self) -> None:
        username = self._username.text()
        password = self._password.text()
        confirm = self._confirm.text()

        errors = validate_all([
            required("Tên đăng nhập", username),
            required("Mật khẩu", password),
            min_length("Mật khẩu", password, 6),
            required("Xác nhận mật khẩu", confirm),
        ])

        if not errors and password != confirm:
            errors.append("Mật khẩu xác nhận không khớp.")

        if errors:
            self._error_lbl.setText("\n".join(errors))
            self._error_lbl.show()
            return

        self._error_lbl.hide()
        self.register_requested.emit(username, password)

    def _show_error(self, msg: str) -> None:
        self._error_lbl.setText(msg)
        self._error_lbl.show()


# ═══════════════════════════════════════════════════════════════════════════════
#  Login Window (main widget)
# ═══════════════════════════════════════════════════════════════════════════════

class LoginWindow(QWidget):
    """
    Cửa sổ đăng nhập / đăng ký — hiện trước AppWindow.
    Nền: login-bg.svg. Card trắng nổi ở giữa, chia đôi 1:1.

    Signals:
        login_success(str) — emit username khi đăng nhập thành công
    """

    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập — My App")
        self.setMinimumSize(680, 420)
        self.resize(760, 440)

        # Load SVG background
        bg_path = os.path.join(_BASE_DIR, "icons", "app", "login-bg.svg")
        self._bg_renderer = QSvgRenderer(bg_path) if os.path.exists(bg_path) else None

        # ── Root layout — căn giữa card ───────────────────────
        root = vbox(spacing=0, margins=(36, 36, 36, 36))
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(root)

        # ── Card container (trắng, bo tròn, shadow) ───────────
        card = QWidget()
        card.setObjectName("loginCard")
        card.setStyleSheet("""
            #loginCard {
                background: transparent;
                border-radius: 10px;
            }
        """)
        card.setMaximumSize(700, 380)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 50))
        card.setGraphicsEffect(shadow)

        card_lay = hbox(spacing=0, margins=theme.MARGIN_ZERO)
        card.setLayout(card_lay)

        # Left: branding panel — tỉ lệ 1
        branding = _BrandingPanel()
        card_lay.addWidget(branding, 1)

        # Right: stacked login/register — tỉ lệ 1 (chia đôi tương xứng)
        right = QWidget()
        right.setStyleSheet("background: transparent; border-top-right-radius: 10px; "
                            "border-bottom-right-radius: 10px;")
        right_lay = vbox(spacing=0, margins=theme.MARGIN_ZERO)
        right_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.setLayout(right_lay)

        self._stack = QStackedWidget()
        self._login_form = _LoginForm()
        self._register_form = _RegisterForm()
        self._stack.addWidget(self._login_form)
        self._stack.addWidget(self._register_form)
        right_lay.addWidget(self._stack)

        card_lay.addWidget(right, 1)
        root.addWidget(card)

        # ── Signals ───────────────────────────────────────────
        self._login_form.switch_to_register.connect(
            lambda: self._stack.setCurrentWidget(self._register_form)
        )
        self._register_form.switch_to_login.connect(
            lambda: self._stack.setCurrentWidget(self._login_form)
        )
        self._login_form.login_requested.connect(self._handle_login)
        self._register_form.register_requested.connect(self._handle_register)

        # Huỷ = đóng cửa sổ
        self._login_form.cancel_requested.connect(self.close)
        self._register_form.cancel_requested.connect(self.close)

        # Load remembered credentials
        self._login_form.load_remembered()

    # ── Background painting ────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        if self._bg_renderer and self._bg_renderer.isValid():
            # SVG phủ toàn bộ cửa sổ, giữ tỉ lệ, căn giữa
            svg_size = self._bg_renderer.defaultSize()
            scale = max(self.width() / svg_size.width(),
                        self.height() / svg_size.height())
            sw = svg_size.width() * scale
            sh = svg_size.height() * scale
            x = (self.width() - sw) / 2
            y = (self.height() - sh) / 2
            self._bg_renderer.render(p, QRectF(x, y, sw, sh))
        else:
            p.fillRect(self.rect(), QColor("#f0ede8"))
        p.end()

    # ── Handlers ───────────────────────────────────────────────

    def _handle_login(self, username: str, password: str, remember: bool) -> None:
        # TODO: Thay bằng logic xác thực thực tế (DB, API)
        if remember:
            settings.set("login/remember", True)
            settings.set("login/username", username)
        else:
            settings.remove("login/remember")
            settings.remove("login/username")

        self.login_success.emit(username)

    def _handle_register(self, username: str, password: str) -> None:
        # TODO: Thay bằng logic tạo tài khoản thực tế (DB, API)
        self._stack.setCurrentWidget(self._login_form)
