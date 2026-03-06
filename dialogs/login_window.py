"""
dialogs/login_window.py — Login / Register window.

Hiển thị trước AppWindow. Đăng nhập thành công emit signal `login_success`.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLineEdit, QCheckBox, QPushButton, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from core import theme
from core.base_widgets import vbox, hbox, label, divider
from utils.validators import required, min_length, validate_all
from utils.settings import settings
from utils.auth import auth
from utils.thread_worker import run_in_thread


# ═══════════════════════════════════════════════════════════════════════════════
#  Login Form
# ═══════════════════════════════════════════════════════════════════════════════

class _LoginForm(QWidget):
    login_requested = pyqtSignal(str, str, bool)   # username, password, remember
    switch_to_register = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        lay = vbox(spacing=theme.SPACING_MD)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(lay)

        # Title
        title = label("Đăng nhập", bold=True, size=theme.FONT_SIZE_LG)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        lay.addWidget(divider())

        # Username
        self._username = QLineEdit()
        self._username.setPlaceholderText("Tên đăng nhập")
        self._username.addAction(
            QIcon("icons/layui/username.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        lay.addWidget(self._username)

        # Password
        self._password = QLineEdit()
        self._password.setPlaceholderText("Mật khẩu")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.addAction(
            QIcon("icons/layui/password.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
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

        # Buttons
        btn_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        btn_cancel = QPushButton("Huỷ")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_lay.addWidget(btn_cancel)
        btn_login = QPushButton("Đăng nhập")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self._on_login)
        btn_lay.addWidget(btn_login)
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

    def _on_cancel(self) -> None:
        self._username.clear()
        self._password.clear()
        self._error_lbl.hide()
        self.window().close()

    def _on_login(self) -> None:
        username = self._username.text().strip()
        password = self._password.text().strip()

        errors = validate_all([
            required("Tên đăng nhập", username),
            required("Mật khẩu", password),
        ])
        if errors:
            self._error_lbl.setText("\n".join(errors))
            self._error_lbl.show()
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
    switch_to_login = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        lay = vbox(spacing=theme.SPACING_MD)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(lay)

        # Title
        title = label("Đăng ký", bold=True, size=theme.FONT_SIZE_LG)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        lay.addWidget(divider())

        # Username
        self._username = QLineEdit()
        self._username.setPlaceholderText("Tên đăng nhập")
        self._username.addAction(
            QIcon("icons/layui/username.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        lay.addWidget(self._username)

        # Password
        self._password = QLineEdit()
        self._password.setPlaceholderText("Mật khẩu")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.addAction(
            QIcon("icons/layui/password.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        lay.addWidget(self._password)

        # Confirm password
        self._confirm = QLineEdit()
        self._confirm.setPlaceholderText("Xác nhận mật khẩu")
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm.addAction(
            QIcon("icons/layui/password.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        lay.addWidget(self._confirm)

        # Error label
        self._error_lbl = QLabel()
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet("color: red;")
        self._error_lbl.hide()
        lay.addWidget(self._error_lbl)

        # Buttons
        btn_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        btn_cancel = QPushButton("Huỷ")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_lay.addWidget(btn_cancel)
        btn_register = QPushButton("Đăng ký")
        btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_register.clicked.connect(self._on_register)
        btn_lay.addWidget(btn_register)
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

    def _on_cancel(self) -> None:
        self._username.clear()
        self._password.clear()
        self._confirm.clear()
        self._error_lbl.hide()
        self.switch_to_login.emit()

    def _on_register(self) -> None:
        username = self._username.text().strip()
        password = self._password.text().strip()
        confirm = self._confirm.text().strip()

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
#  Login Window
# ═══════════════════════════════════════════════════════════════════════════════

class LoginWindow(QWidget):
    """
    Cửa sổ đăng nhập / đăng ký — hiện trước AppWindow.

    Signals:
        login_success(str) — emit username khi đăng nhập thành công
    """

    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập")
        self.setFixedSize(360, 420)

        root = vbox(spacing=0, margins=theme.MARGIN_DIALOG)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(root)

        # Stacked: login / register
        self._stack = QStackedWidget()
        self._login_form = _LoginForm()
        self._register_form = _RegisterForm()
        self._stack.addWidget(self._login_form)
        self._stack.addWidget(self._register_form)
        root.addWidget(self._stack)

        # Signals
        self._login_form.switch_to_register.connect(
            lambda: self._stack.setCurrentWidget(self._register_form)
        )
        self._register_form.switch_to_login.connect(
            lambda: self._stack.setCurrentWidget(self._login_form)
        )
        self._login_form.login_requested.connect(self._handle_login)
        self._register_form.register_requested.connect(self._handle_register)

        # Load remembered credentials
        self._login_form.load_remembered()

    # ── Handlers ─────────────────────────────────────────────────

    def _handle_login(self, username: str, password: str, remember: bool) -> None:
        self._set_busy(True)
        self._remember_pending = remember
        self._username_pending = username
        run_in_thread(
            lambda: auth.login(username, password),
            on_result=self._on_login_result,
            on_error=lambda e: self._on_auth_error(e, is_login=True),
            on_finished=lambda: self._set_busy(False),
        )

    def _on_login_result(self, result: tuple[bool, str]) -> None:
        ok, msg = result
        if ok:
            if self._remember_pending:
                settings.set("login/remember", True)
                settings.set("login/username", self._username_pending)
            else:
                settings.remove("login/remember")
                settings.remove("login/username")
            self.login_success.emit(msg)  # msg = username
        else:
            self._login_form._show_error(msg)

    def _handle_register(self, username: str, password: str) -> None:
        self._set_busy(True)
        run_in_thread(
            lambda: auth.register(username, password),
            on_result=self._on_register_result,
            on_error=lambda e: self._on_auth_error(e, is_login=False),
            on_finished=lambda: self._set_busy(False),
        )

    def _on_register_result(self, result: tuple[bool, str]) -> None:
        ok, msg = result
        if ok:
            self._stack.setCurrentWidget(self._login_form)
            self._login_form._show_error("")
            self._login_form._error_lbl.setStyleSheet("color: green;")
            self._login_form._error_lbl.setText("Đăng ký thành công! Hãy đăng nhập.")
            self._login_form._error_lbl.show()
        else:
            self._register_form._show_error(msg)

    def _on_auth_error(self, error_msg: str, is_login: bool) -> None:
        form = self._login_form if is_login else self._register_form
        form._show_error("Không thể kết nối máy chủ.")

    def _set_busy(self, busy: bool) -> None:
        self._stack.setEnabled(not busy)
