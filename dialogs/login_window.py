"""
dialogs/login_window.py — Login / Register window.

Hiển thị trước AppWindow. Đăng nhập thành công emit signal `login_success`.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLineEdit, QCheckBox, QPushButton, QLabel, QProgressBar, QComboBox,
    QGraphicsDropShadowEffect, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QIcon, QColor, QLinearGradient, QPainter, QPalette, QFont
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication as _QApp

from core import theme
from core.i18n import t, set_language, get_language, get_languages
from core.base_widgets import vbox, hbox, label, divider
from utils.validators import required, min_length, validate_all
from utils.settings import settings
from utils.auth import auth
from utils.thread_worker import run_in_thread


_ACCENT = "#0078d4"       # Windows accent blue
_ACCENT_HOVER = "#106ebe"
_ACCENT_PRESSED = "#005a9e"


def _style_primary_btn(btn: QPushButton) -> None:
    """Style nút chính (Đăng nhập / Đăng ký) với màu accent."""
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {_ACCENT};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {_ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {_ACCENT_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: #ccc;
            color: #888;
        }}
    """)


class _GradientHeader(QWidget):
    """Banner gradient phía trên form login với logo MaxHub."""

    _LOGO_PATH = "icons/app/logo-maxhub-white.svg"
    _HEADER_H = 90

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._text = text
        self._svg = QSvgRenderer(self._LOGO_PATH)
        self.setFixedHeight(self._HEADER_H)

    def set_text(self, text: str) -> None:
        self._text = text
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w, h = self.width(), self.height()

        # Gradient background
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(_ACCENT))
        grad.setColorAt(1.0, QColor("#00b4d8"))
        p.fillRect(self.rect(), grad)

        # Logo — fit to header, centered
        if self._svg.isValid():
            svg_w, svg_h = self._svg.defaultSize().width(), self._svg.defaultSize().height()
            # Scale logo to fit within header with padding
            pad = 16
            avail_w, avail_h = w - pad * 2, h - pad * 2
            scale = min(avail_w / svg_w, avail_h / svg_h)
            logo_w, logo_h = svg_w * scale, svg_h * scale
            x = (w - logo_w) / 2
            y = (h - logo_h) / 2
            self._svg.render(p, QRectF(x, y, logo_w, logo_h))
        else:
            # Fallback: text
            p.setPen(QColor("white"))
            f = theme.font(size=theme.FONT_SIZE_XL, bold=True)
            p.setFont(f)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)

        p.end()


class _IllustrationPanel(QWidget):
    """Left panel: gradient background + SVG illustration + headline + description."""

    _BG_SVG = "icons/app/login-bg.svg"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(380)
        self._svg = QSvgRenderer(self._BG_SVG)
        self._headline = t("login.headline")
        self._description = t("login.description")

    def set_texts(self, headline: str, description: str) -> None:
        self._headline = headline
        self._description = description
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w, h = self.width(), self.height()

        # Gradient background
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(_ACCENT))
        grad.setColorAt(1.0, QColor("#00b4d8"))
        p.fillRect(self.rect(), grad)

        # SVG illustration — centered in upper portion
        if self._svg.isValid():
            svg_w, svg_h = self._svg.defaultSize().width(), self._svg.defaultSize().height()
            pad = 30
            avail_w = w - pad * 2
            avail_h = h * 0.55  # use top 55% for illustration
            scale = min(avail_w / svg_w, avail_h / svg_h)
            logo_w, logo_h = svg_w * scale, svg_h * scale
            x = (w - logo_w) / 2
            y = pad + (avail_h - logo_h) / 2
            self._svg.render(p, QRectF(x, y, logo_w, logo_h))

        # Headline text
        p.setPen(QColor("white"))
        headline_y = int(h * 0.60)
        headline_font = theme.font(size=theme.FONT_SIZE_LG, bold=True)
        p.setFont(headline_font)
        headline_rect = self.rect().adjusted(24, headline_y, -24, 0)
        p.drawText(
            headline_rect,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap,
            self._headline,
        )

        # Description text — below headline
        desc_color = QColor(255, 255, 255, 180)
        p.setPen(desc_color)
        desc_font = theme.font(size=theme.FONT_SIZE_SM)
        p.setFont(desc_font)
        desc_rect = self.rect().adjusted(24, headline_y + 40, -24, -16)
        p.drawText(
            desc_rect,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap,
            self._description,
        )

        p.end()


def _add_eye_toggle(line_edit: QLineEdit) -> None:
    """Them icon con mat ben phai de toggle hien/an password."""
    icon_hide = QIcon("icons/layui/eye-invisible.svg")
    icon_show = QIcon("icons/layui/eye.svg")
    action = line_edit.addAction(icon_hide, QLineEdit.ActionPosition.TrailingPosition)

    def toggle():
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(icon_show)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(icon_hide)

    action.triggered.connect(toggle)


# ═══════════════════════════════════════════════════════════════════════════════
#  Login Form
# ═══════════════════════════════════════════════════════════════════════════════

class _LoginForm(QWidget):
    login_requested = pyqtSignal(str, str, bool)   # username, password, remember
    switch_to_register = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        lay = vbox(spacing=theme.SPACING_MD)
        self.setLayout(lay)

        # Gradient header
        self._header = _GradientHeader(t("login.title"))
        lay.addWidget(self._header)
        lay.addSpacing(theme.SPACING_MD)

        # Username
        self._username = QLineEdit()
        self._username.setPlaceholderText(t("login.username"))
        self._username.addAction(
            QIcon("icons/layui/username.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        lay.addWidget(self._username)

        # Password
        self._password = QLineEdit()
        self._password.setPlaceholderText(t("login.password"))
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.addAction(
            QIcon("icons/layui/password.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._password)
        lay.addWidget(self._password)

        # Enter key triggers login
        self._username.returnPressed.connect(self._on_login)
        self._password.returnPressed.connect(self._on_login)

        # Remember me
        self._remember = QCheckBox(t("login.remember"))
        lay.addWidget(self._remember)

        # Error label
        self._error_lbl = QLabel()
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet(f"color: #d32f2f; background: #fde8e8; padding: 6px; border-radius: 4px;")
        self._error_lbl.hide()
        lay.addWidget(self._error_lbl)

        # Buttons
        btn_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        self._btn_cancel = QPushButton(t("login.btn_cancel"))
        self._btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cancel.clicked.connect(self._on_cancel)
        btn_lay.addWidget(self._btn_cancel)
        self._btn_login = QPushButton(t("login.btn_login"))
        self._btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_login.clicked.connect(self._on_login)
        _style_primary_btn(self._btn_login)
        btn_lay.addWidget(self._btn_login)
        lay.addLayout(btn_lay)

        lay.addStretch()

        # Switch link
        switch_lay = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
        switch_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_account_lbl = label(t("login.no_account"))
        switch_lay.addWidget(self._no_account_lbl)
        self._link_register = QPushButton(t("login.link_register"))
        self._link_register.setFlat(True)
        self._link_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self._link_register.setStyleSheet(f"color: {_ACCENT}; text-decoration: underline;")
        self._link_register.clicked.connect(self.switch_to_register.emit)
        switch_lay.addWidget(self._link_register)
        lay.addLayout(switch_lay)

    def retranslate(self) -> None:
        self._header.set_text(t("login.title"))
        self._username.setPlaceholderText(t("login.username"))
        self._password.setPlaceholderText(t("login.password"))
        self._remember.setText(t("login.remember"))
        self._btn_cancel.setText(t("login.btn_cancel"))
        self._btn_login.setText(t("login.btn_login"))
        self._no_account_lbl.setText(t("login.no_account"))
        self._link_register.setText(t("login.link_register"))

    def _on_cancel(self) -> None:
        self._username.clear()
        self._password.clear()
        self._error_lbl.hide()
        _QApp.quit()

    def _on_login(self) -> None:
        username = self._username.text().strip()
        password = self._password.text().strip()

        errors = validate_all([
            required(t("login.username"), username),
            required(t("login.password"), password),
        ])
        if errors:
            self._error_lbl.setText("\n".join(errors))
            self._error_lbl.show()
            return

        self._error_lbl.hide()
        self.login_requested.emit(username, password, self._remember.isChecked())

    def _show_error(self, msg: str) -> None:
        self._error_lbl.setStyleSheet("color: #d32f2f; background: #fde8e8; padding: 6px; border-radius: 4px;")
        self._error_lbl.setText(msg)
        self._error_lbl.show()

    def _show_success(self, msg: str) -> None:
        self._error_lbl.setStyleSheet("color: #2e7d32; background: #e8f5e9; padding: 6px; border-radius: 4px;")
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
        self.setLayout(lay)

        # Gradient header
        self._header = _GradientHeader(t("register.title"))
        lay.addWidget(self._header)
        lay.addSpacing(theme.SPACING_MD)

        # Username
        self._username = QLineEdit()
        self._username.setPlaceholderText(t("register.username"))
        self._username.addAction(
            QIcon("icons/layui/username.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        lay.addWidget(self._username)

        # Password
        self._password = QLineEdit()
        self._password.setPlaceholderText(t("register.password"))
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.addAction(
            QIcon("icons/layui/password.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._password)
        lay.addWidget(self._password)

        # Confirm password
        self._confirm = QLineEdit()
        self._confirm.setPlaceholderText(t("register.confirm_password"))
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm.addAction(
            QIcon("icons/layui/password.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._confirm)
        lay.addWidget(self._confirm)

        # Error label
        self._error_lbl = QLabel()
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet(f"color: #d32f2f; background: #fde8e8; padding: 6px; border-radius: 4px;")
        self._error_lbl.hide()
        lay.addWidget(self._error_lbl)

        # Buttons
        btn_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        self._btn_cancel = QPushButton(t("register.btn_cancel"))
        self._btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cancel.clicked.connect(self._on_cancel)
        btn_lay.addWidget(self._btn_cancel)
        self._btn_register = QPushButton(t("register.btn_register"))
        self._btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_register.clicked.connect(self._on_register)
        _style_primary_btn(self._btn_register)
        btn_lay.addWidget(self._btn_register)
        lay.addLayout(btn_lay)

        lay.addStretch()

        # Switch link
        switch_lay = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
        switch_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._has_account_lbl = label(t("register.has_account"))
        switch_lay.addWidget(self._has_account_lbl)
        self._link_login = QPushButton(t("register.link_login"))
        self._link_login.setFlat(True)
        self._link_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self._link_login.setStyleSheet(f"color: {_ACCENT}; text-decoration: underline;")
        self._link_login.clicked.connect(self.switch_to_login.emit)
        switch_lay.addWidget(self._link_login)
        lay.addLayout(switch_lay)

    def retranslate(self) -> None:
        self._header.set_text(t("register.title"))
        self._username.setPlaceholderText(t("register.username"))
        self._password.setPlaceholderText(t("register.password"))
        self._confirm.setPlaceholderText(t("register.confirm_password"))
        self._btn_cancel.setText(t("register.btn_cancel"))
        self._btn_register.setText(t("register.btn_register"))
        self._has_account_lbl.setText(t("register.has_account"))
        self._link_login.setText(t("register.link_login"))

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
            required(t("register.username"), username),
            required(t("register.password"), password),
            min_length(t("register.password"), password, 6),
            required(t("register.confirm_password"), confirm),
        ])

        if not errors and password != confirm:
            errors.append(t("register.password_mismatch"))

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
        self.setWindowTitle(t("login.title"))
        self.setFixedSize(760, 490)

        root = hbox(spacing=0, margins=theme.MARGIN_ZERO)
        self.setLayout(root)

        # Left: illustration panel
        self._illustration = _IllustrationPanel()
        root.addWidget(self._illustration)

        # Right: form column
        right = vbox(spacing=0, margins=theme.MARGIN_ZERO)

        # Stacked: login / register
        self._stack = QStackedWidget()
        self._login_form = _LoginForm()
        self._register_form = _RegisterForm()
        self._stack.addWidget(self._login_form)
        self._stack.addWidget(self._register_form)
        right.addWidget(self._stack, 1)

        # Loading bar — indeterminate, ẩn mặc định
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
        self._progress.hide()
        right.addWidget(self._progress)

        # Language selector — bottom of window
        lang_lay = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
        lang_lay.addStretch()
        lang_lay.addWidget(QLabel("🌐"))
        self._lang_combo = QComboBox()
        languages = get_languages()
        self._lang_codes = list(languages.keys())
        self._lang_combo.addItems(list(languages.values()))
        current_idx = self._lang_codes.index(get_language()) if get_language() in self._lang_codes else 0
        self._lang_combo.setCurrentIndex(current_idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_lay.addWidget(self._lang_combo)
        lang_lay.addStretch()
        right.addLayout(lang_lay)

        # Version label
        from utils.updater import APP_VERSION
        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet("color: #999; font-size: 8pt; padding: 4px;")
        right.addWidget(ver_lbl)

        root.addLayout(right)

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

    # ── Language ──────────────────────────────────────────────────

    def _on_language_changed(self, index: int) -> None:
        lang = self._lang_codes[index]
        set_language(lang)
        self._retranslate()

    def _retranslate(self) -> None:
        self.setWindowTitle(t("login.title"))
        self._login_form.retranslate()
        self._register_form.retranslate()
        self._illustration.set_texts(t("login.headline"), t("login.description"))

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
            from utils.api import api
            if self._remember_pending:
                settings.set("login/remember", True)
                settings.set("login/username", self._username_pending)
                api.save_session()  # luu JWT de auto-login lan sau
            else:
                settings.remove("login/remember")
                settings.remove("login/username")
                api.clear_session()
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
            self._login_form._show_success(t("register.success"))
        else:
            self._register_form._show_error(msg)

    def _on_auth_error(self, error_msg: str, is_login: bool) -> None:
        form = self._login_form if is_login else self._register_form
        form._show_error(t("login.error_connect"))

    def _set_busy(self, busy: bool) -> None:
        self._stack.setEnabled(not busy)
        self._progress.setVisible(busy)
