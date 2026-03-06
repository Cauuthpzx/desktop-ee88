"""
dialogs/login_window.py — Login / Register window.

Hiển thị trước AppWindow. Đăng nhập thành công emit signal `login_success`.
Dark-themed frameless window 600x400 | Left 300 (branding) | Right 300 (form)
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLineEdit, QCheckBox, QPushButton, QLabel, QProgressBar, QComboBox,
    QGraphicsDropShadowEffect, QFrame,
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QByteArray, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import QColor, QPainter, QPalette
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication as _QApp

from core.i18n import t, set_language, get_language, get_languages
from utils.validators import required, min_length, validate_all
from utils.settings import settings
from utils.auth import auth
from utils.thread_worker import run_in_thread


# ─── SVG Icon-only logo ───────────────────────────────────
_ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-80 -80 160 160" width="160" height="160">
  <defs>
    <linearGradient id="r1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#00BFFF"/><stop offset="100%" style="stop-color:#1565C0"/></linearGradient>
    <linearGradient id="r2" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#42A5F5"/><stop offset="70%" style="stop-color:#1976D2"/><stop offset="100%" style="stop-color:#E67E22"/></linearGradient>
    <linearGradient id="r3" x1="100%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:#4FC3F7"/><stop offset="100%" style="stop-color:#1E88E5"/></linearGradient>
    <linearGradient id="b1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#29B6F6"/><stop offset="100%" style="stop-color:#0D47A1"/></linearGradient>
    <linearGradient id="b2" x1="100%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:#4FC3F7"/><stop offset="100%" style="stop-color:#1565C0"/></linearGradient>
    <linearGradient id="b3" x1="50%" y1="100%" x2="50%" y2="0%"><stop offset="0%" style="stop-color:#0288D1"/><stop offset="100%" style="stop-color:#01579B"/></linearGradient>
    <filter id="sg" x="-25%" y="-25%" width="150%" height="150%"><feGaussianBlur stdDeviation="2.5" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
    <filter id="ng" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
    <filter id="og" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3.5" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
  </defs>
  <g filter="url(#sg)"><ellipse rx="62" ry="34" fill="none" stroke="url(#r1)" stroke-width="4" opacity="0.85"/></g>
  <g filter="url(#sg)"><ellipse rx="62" ry="34" fill="none" stroke="url(#r2)" stroke-width="4" opacity="0.85" transform="rotate(60)"/></g>
  <g filter="url(#sg)"><ellipse rx="62" ry="34" fill="none" stroke="url(#r3)" stroke-width="4" opacity="0.85" transform="rotate(120)"/></g>
  <path d="M-3,-6 C-18,-30 -8,-40 0,-22 C8,-40 18,-30 3,-6 Z" fill="url(#b1)" opacity="0.9"/>
  <path d="M-3,-6 C-18,-30 -8,-40 0,-22 C8,-40 18,-30 3,-6 Z" fill="url(#b2)" opacity="0.9" transform="rotate(120)"/>
  <path d="M-3,-6 C-18,-30 -8,-40 0,-22 C8,-40 18,-30 3,-6 Z" fill="url(#b3)" opacity="0.9" transform="rotate(240)"/>
  <circle r="5" fill="#E3F2FD" opacity="0.7"/>
  <g filter="url(#ng)"><circle cy="-62" r="6" fill="#4FC3F7"/><circle cy="-62" r="2.5" fill="white"/></g>
  <g filter="url(#ng)"><circle cx="53.7" cy="-31" r="6" fill="#29B6F6"/><circle cx="53.7" cy="-31" r="2.5" fill="white"/></g>
  <g filter="url(#og)"><circle cx="53.7" cy="31" r="6.5" fill="#F57C00"/><circle cx="53.7" cy="31" r="2.5" fill="#FFE0B2"/></g>
  <g filter="url(#ng)"><circle cy="62" r="6" fill="#0288D1"/><circle cy="62" r="2.5" fill="white"/></g>
  <g filter="url(#ng)"><circle cx="-53.7" cy="31" r="6" fill="#1565C0"/><circle cx="-53.7" cy="31" r="2.5" fill="white"/></g>
  <g filter="url(#og)"><circle cx="-53.7" cy="-31" r="6.5" fill="#FF9800"/><circle cx="-53.7" cy="-31" r="2.5" fill="#FFF3E0"/></g>
</svg>'''

_SVG_USER = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
</svg>'''

_SVG_LOCK = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
</svg>'''

_SVG_SHIELD = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>
</svg>'''


# ─── Colors ────────────────────────────────────────────────
class _C:
    BG_DARK    = "#0B0E17"
    BG_CARD    = "#111827"
    BG_LEFT    = "#0C1018"
    BG_INPUT   = "#1A2236"
    BORDER     = "#1E3050"
    FOCUS      = "#00BCD4"
    CYAN       = "#00E5FF"
    CYAN_DIM   = "#00838F"
    BLUE       = "#2196F3"
    ORANGE     = "#F57C00"
    TEXT       = "#E8EDF5"
    TEXT_DIM   = "#7B8CA8"
    TEXT_MUTED = "#4A5B78"
    WHITE      = "#FFFFFF"
    ERROR      = "#EF5350"
    SUCCESS    = "#66BB6A"


# ─── Helpers ───────────────────────────────────────────────
def _shadow(color: str = "#000", blur: int = 20, y: int = 4,
            parent: QWidget | None = None) -> QGraphicsDropShadowEffect:
    s = QGraphicsDropShadowEffect(parent)
    s.setColor(QColor(color))
    s.setBlurRadius(blur)
    s.setOffset(0, y)
    return s


def _svg_to_pixmap(svg_str: str, size: int, color: str = "#4A5B78"):
    from PyQt6.QtGui import QPixmap
    svg_str = svg_str.replace("{color}", color)
    renderer = QSvgRenderer(QByteArray(svg_str.encode()))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p)
    p.end()
    return pm


# ─── IconInput ─────────────────────────────────────────────
class _IconInput(QFrame):
    """Input field with SVG icon on the left."""

    def __init__(self, icon_svg: str, placeholder: str = "",
                 is_password: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._style_normal = f"_IconInput {{ background:{_C.BG_INPUT}; border:1.5px solid {_C.BORDER}; border-radius:8px; }}"
        self._style_focus = f"_IconInput {{ background:{_C.BG_INPUT}; border:1.5px solid {_C.FOCUS}; border-radius:8px; }}"
        self.setStyleSheet(self._style_normal)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(8)

        icon_label = QLabel()
        icon_label.setFixedSize(18, 18)
        icon_label.setPixmap(_svg_to_pixmap(icon_svg, 18, _C.TEXT_MUTED))
        icon_label.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(icon_label)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        if is_password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background:transparent; border:none; color:{_C.TEXT};
                font-size:12.5px; font-family:'Segoe UI',sans-serif; padding:0;
                selection-background-color:{_C.CYAN_DIM};
            }}
            QLineEdit::placeholder {{ color:{_C.TEXT_MUTED}; }}
        """)
        lay.addWidget(self.input)
        self.input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.input:
            if event.type() == event.Type.FocusIn:
                self.setStyleSheet(self._style_focus)
            elif event.type() == event.Type.FocusOut:
                self.setStyleSheet(self._style_normal)
        return super().eventFilter(obj, event)

    def text(self) -> str:
        return self.input.text().strip()

    def clear(self) -> None:
        self.input.clear()

    def setPlaceholderText(self, text: str) -> None:
        self.input.setPlaceholderText(text)


# ─── Styled Buttons ───────────────────────────────────────
def _primary_btn_style(cyan: bool = True) -> str:
    if cyan:
        return f"""
            QPushButton {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00BCD4, stop:1 #0097A7);
                border:none; border-radius:8px; color:{_C.WHITE};
                font-size:13px; font-weight:700; font-family:'Segoe UI'; letter-spacing:0.5px;
            }}
            QPushButton:hover {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00E5FF, stop:1 #00BCD4); }}
            QPushButton:pressed {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0097A7, stop:1 #00838F); }}
            QPushButton:disabled {{ background:#333; color:#666; }}
        """
    return f"""
        QPushButton {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #F57C00, stop:1 #E65100);
            border:none; border-radius:8px; color:{_C.WHITE};
            font-size:13px; font-weight:700; font-family:'Segoe UI'; letter-spacing:0.5px;
        }}
        QPushButton:hover {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #FF9800, stop:1 #F57C00); }}
        QPushButton:pressed {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #E65100, stop:1 #BF360C); }}
        QPushButton:disabled {{ background:#333; color:#666; }}
    """


class _LinkLabel(QLabel):
    """Clickable link label with hover effect."""

    clicked = pyqtSignal()

    def __init__(self, text: str, color: str = _C.CYAN_DIM, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color = color
        self._base = f"color:{color}; font-size:11px; font-family:'Segoe UI'; background:transparent;"
        self.setStyleSheet(self._base)

    def enterEvent(self, e) -> None:
        self.setStyleSheet(f"color:{_C.CYAN}; font-size:11px; font-family:'Segoe UI'; background:transparent; text-decoration:underline;")

    def leaveEvent(self, e) -> None:
        self.setStyleSheet(self._base)

    def mousePressEvent(self, e) -> None:
        self.clicked.emit()


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{_C.TEXT_DIM}; font-size:10.5px; font-weight:600; font-family:'Segoe UI';")
    return lbl


def _error_label() -> QLabel:
    lbl = QLabel()
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"color:{_C.ERROR}; font-size:10.5px; font-family:'Segoe UI'; min-height:16px;")
    lbl.hide()
    return lbl


# ═══════════════════════════════════════════════════════════════════════════════
#  Login Form
# ═══════════════════════════════════════════════════════════════════════════════

class _LoginForm(QWidget):
    login_requested = pyqtSignal(str, str, bool)   # username, password, remember
    switch_to_register = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 0, 28, 0)
        lay.setSpacing(0)

        lay.addStretch(2)

        # Header
        self._title = QLabel(t("login.title"))
        self._title.setStyleSheet(f"color:{_C.TEXT}; font-size:22px; font-weight:800; font-family:'Segoe UI';")
        lay.addWidget(self._title)
        lay.addSpacing(3)

        self._subtitle = QLabel(t("login.username"))
        self._subtitle.setStyleSheet(f"color:{_C.TEXT_DIM}; font-size:11.5px; font-family:'Segoe UI';")
        lay.addWidget(self._subtitle)
        lay.addSpacing(20)

        # Username
        self._user_lbl = _field_label(t("login.username"))
        lay.addWidget(self._user_lbl)
        lay.addSpacing(4)
        self._username = _IconInput(_SVG_USER, t("login.username"))
        lay.addWidget(self._username)
        lay.addSpacing(12)

        # Password
        self._pwd_lbl = _field_label(t("login.password"))
        lay.addWidget(self._pwd_lbl)
        lay.addSpacing(4)
        self._password = _IconInput(_SVG_LOCK, t("login.password"), is_password=True)
        lay.addWidget(self._password)
        lay.addSpacing(8)

        # Enter key triggers login
        self._username.input.returnPressed.connect(self._on_login)
        self._password.input.returnPressed.connect(self._on_login)

        # Remember me
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        self._remember = QLabel()
        self._remember._checked = False
        self._update_remember_text()
        self._remember.setStyleSheet(f"color:{_C.TEXT_MUTED}; font-size:10.5px; font-family:'Segoe UI';")
        self._remember.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remember.mousePressEvent = lambda e: self._toggle_remember()
        row.addWidget(self._remember)
        row.addStretch()
        lay.addLayout(row)
        lay.addSpacing(18)

        # Error label
        self._error_lbl = _error_label()
        lay.addWidget(self._error_lbl)
        lay.addSpacing(4)

        # Login button
        self._btn_login = QPushButton(t("login.btn_login").upper())
        self._btn_login.setFixedHeight(40)
        self._btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_login.setStyleSheet(_primary_btn_style(cyan=True))
        self._btn_login.setGraphicsEffect(_shadow("#00BCD4", 20, 3))
        self._btn_login.clicked.connect(self._on_login)
        lay.addWidget(self._btn_login)
        lay.addSpacing(14)

        # Switch link
        switch_row = QHBoxLayout()
        switch_row.setContentsMargins(0, 0, 0, 0)
        switch_row.addStretch()
        self._no_account_lbl = QLabel(t("login.no_account"))
        self._no_account_lbl.setStyleSheet(f"color:{_C.TEXT_MUTED}; font-size:11px; font-family:'Segoe UI';")
        switch_row.addWidget(self._no_account_lbl)
        switch_row.addSpacing(4)
        self._link_register = _LinkLabel(t("login.link_register"), _C.ORANGE)
        self._link_register.clicked.connect(self.switch_to_register.emit)
        switch_row.addWidget(self._link_register)
        switch_row.addStretch()
        lay.addLayout(switch_row)

        lay.addStretch(3)

    def _toggle_remember(self) -> None:
        self._remember._checked = not self._remember._checked
        self._update_remember_text()

    def _update_remember_text(self) -> None:
        check = "☑" if self._remember._checked else "☐"
        self._remember.setText(f"{check} {t('login.remember')}")

    def is_remembered(self) -> bool:
        return self._remember._checked

    def retranslate(self) -> None:
        self._title.setText(t("login.title"))
        self._subtitle.setText(t("login.username"))
        self._user_lbl.setText(t("login.username"))
        self._username.setPlaceholderText(t("login.username"))
        self._pwd_lbl.setText(t("login.password"))
        self._password.setPlaceholderText(t("login.password"))
        self._update_remember_text()
        self._btn_login.setText(t("login.btn_login").upper())
        self._no_account_lbl.setText(t("login.no_account"))
        self._link_register.setText(t("login.link_register"))

    def _on_login(self) -> None:
        username = self._username.text()
        password = self._password.text()

        errors = validate_all([
            required(t("login.username"), username),
            required(t("login.password"), password),
        ])
        if errors:
            self._show_error("\n".join(errors))
            return

        self._error_lbl.hide()
        self.login_requested.emit(username, password, self.is_remembered())

    def _show_error(self, msg: str) -> None:
        self._error_lbl.setStyleSheet(f"color:{_C.ERROR}; font-size:10.5px; font-family:'Segoe UI';")
        self._error_lbl.setText(msg)
        self._error_lbl.show()

    def _show_success(self, msg: str) -> None:
        self._error_lbl.setStyleSheet(f"color:{_C.SUCCESS}; font-size:10.5px; font-family:'Segoe UI';")
        self._error_lbl.setText(msg)
        self._error_lbl.show()

    def load_remembered(self) -> None:
        if settings.get_bool("login/remember"):
            self._username.input.setText(settings.get_str("login/username"))
            self._remember._checked = True
            self._update_remember_text()
            self._password.input.setFocus()


# ═══════════════════════════════════════════════════════════════════════════════
#  Register Form
# ═══════════════════════════════════════════════════════════════════════════════

class _RegisterForm(QWidget):
    register_requested = pyqtSignal(str, str)  # username, password
    switch_to_login = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 0, 28, 0)
        lay.setSpacing(0)

        lay.addStretch(2)

        # Header
        self._title = QLabel(t("register.title"))
        self._title.setStyleSheet(f"color:{_C.TEXT}; font-size:22px; font-weight:800; font-family:'Segoe UI';")
        lay.addWidget(self._title)
        lay.addSpacing(3)

        self._subtitle = QLabel(t("register.username"))
        self._subtitle.setStyleSheet(f"color:{_C.TEXT_DIM}; font-size:11.5px; font-family:'Segoe UI';")
        lay.addWidget(self._subtitle)
        lay.addSpacing(16)

        # Username
        self._user_lbl = _field_label(t("register.username"))
        lay.addWidget(self._user_lbl)
        lay.addSpacing(3)
        self._username = _IconInput(_SVG_USER, t("register.username"))
        lay.addWidget(self._username)
        lay.addSpacing(10)

        # Password
        self._pwd_lbl = _field_label(t("register.password"))
        lay.addWidget(self._pwd_lbl)
        lay.addSpacing(3)
        self._password = _IconInput(_SVG_LOCK, t("register.password"), is_password=True)
        lay.addWidget(self._password)
        lay.addSpacing(10)

        # Confirm password
        self._confirm_lbl = _field_label(t("register.confirm_password"))
        lay.addWidget(self._confirm_lbl)
        lay.addSpacing(3)
        self._confirm = _IconInput(_SVG_SHIELD, t("register.confirm_password"), is_password=True)
        lay.addWidget(self._confirm)

        # Error label
        self._error_lbl = _error_label()
        lay.addSpacing(4)
        lay.addWidget(self._error_lbl)
        lay.addSpacing(6)

        # Register button
        self._btn_register = QPushButton(t("register.btn_register").upper())
        self._btn_register.setFixedHeight(40)
        self._btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_register.setStyleSheet(_primary_btn_style(cyan=False))
        self._btn_register.setGraphicsEffect(_shadow("#F57C00", 20, 3))
        self._btn_register.clicked.connect(self._on_register)
        lay.addWidget(self._btn_register)
        lay.addSpacing(12)

        # Switch link
        switch_row = QHBoxLayout()
        switch_row.setContentsMargins(0, 0, 0, 0)
        switch_row.addStretch()
        self._has_account_lbl = QLabel(t("register.has_account"))
        self._has_account_lbl.setStyleSheet(f"color:{_C.TEXT_MUTED}; font-size:11px; font-family:'Segoe UI';")
        switch_row.addWidget(self._has_account_lbl)
        switch_row.addSpacing(4)
        self._link_login = _LinkLabel(t("register.link_login"), _C.CYAN_DIM)
        self._link_login.clicked.connect(self.switch_to_login.emit)
        switch_row.addWidget(self._link_login)
        switch_row.addStretch()
        lay.addLayout(switch_row)

        lay.addStretch(2)

    def retranslate(self) -> None:
        self._title.setText(t("register.title"))
        self._subtitle.setText(t("register.username"))
        self._user_lbl.setText(t("register.username"))
        self._username.setPlaceholderText(t("register.username"))
        self._pwd_lbl.setText(t("register.password"))
        self._password.setPlaceholderText(t("register.password"))
        self._confirm_lbl.setText(t("register.confirm_password"))
        self._confirm.setPlaceholderText(t("register.confirm_password"))
        self._btn_register.setText(t("register.btn_register").upper())
        self._has_account_lbl.setText(t("register.has_account"))
        self._link_login.setText(t("register.link_login"))

    def _on_register(self) -> None:
        username = self._username.text()
        password = self._password.text()
        confirm = self._confirm.text()

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
    Frameless dark-themed login/register window.

    Signals:
        login_success(str) — emit username khi đăng nhập thành công
    """

    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("login.title"))
        self.setFixedSize(600, 400)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Card container
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            #card {{
                background: {_C.BG_CARD};
                border-radius: 16px;
                border: 1px solid {_C.BORDER};
            }}
        """)
        card.setGraphicsEffect(_shadow("#000", 45, 10, card))
        root.addWidget(card)

        card_lay = QHBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # ═══ LEFT PANEL (branding) ═══
        left = QFrame()
        left.setFixedWidth(300)
        left.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {_C.BG_DARK}, stop:1 #0D1220);
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
                border-right: 1px solid {_C.BORDER};
            }}
        """)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(24, 24, 24, 18)
        ll.setSpacing(0)

        # Logo
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setPixmap(_svg_to_pixmap(_ICON_SVG, 80, ""))
        ll.addWidget(logo_lbl)
        ll.addSpacing(12)

        # Title
        title = QLabel()
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setText(
            f'<span style="font-family:Segoe UI; font-size:20px; font-weight:900; color:{_C.TEXT};">Max</span>'
            f'<span style="font-family:Segoe UI; font-size:20px; font-weight:900; color:{_C.CYAN};"> HUB</span>'
            f'<span style="font-family:Segoe UI; font-size:20px; font-weight:400; color:{_C.TEXT_DIM};"> Admin</span>'
        )
        ll.addWidget(title)
        ll.addSpacing(8)

        # Accent line
        line = QFrame()
        line.setFixedHeight(3)
        line.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #00BCD4, stop:0.5 #2196F3, stop:1 #F57C00);
            border-radius: 1px; margin: 0 40px;
        """)
        ll.addWidget(line)
        ll.addSpacing(12)

        # Headline
        self._headline = QLabel(t("login.headline"))
        self._headline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._headline.setWordWrap(True)
        self._headline.setStyleSheet(f"color:{_C.TEXT_DIM}; font-size:12px; font-family:'Segoe UI'; font-weight:600;")
        ll.addWidget(self._headline)
        ll.addSpacing(10)

        # Description
        self._description = QLabel(t("login.description"))
        self._description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._description.setWordWrap(True)
        self._description.setStyleSheet(f"color:{_C.TEXT_MUTED}; font-size:10px; font-family:'Segoe UI'; line-height:15px; padding:0 8px;")
        ll.addWidget(self._description)

        ll.addStretch()

        # Circuit decoration
        circuit = QLabel()
        circuit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circuit.setTextFormat(Qt.TextFormat.RichText)
        circuit.setText(
            f'<span style="color:{_C.TEXT_MUTED}; font-size:9px; font-family:Consolas,monospace; letter-spacing:2px;">'
            '── ◉ ── ◈ ── ◉ ──</span>'
        )
        ll.addWidget(circuit)
        ll.addSpacing(6)

        # Language selector + version
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addStretch()
        self._lang_combo = QComboBox()
        self._lang_combo.setStyleSheet(f"""
            QComboBox {{
                background: {_C.BG_INPUT}; color: {_C.TEXT_DIM};
                border: 1px solid {_C.BORDER}; border-radius: 4px;
                padding: 2px 6px; font-size: 9px; font-family: 'Segoe UI';
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {_C.BG_CARD}; color: {_C.TEXT};
                selection-background-color: {_C.CYAN_DIM};
                border: 1px solid {_C.BORDER};
            }}
        """)
        languages = get_languages()
        self._lang_codes = list(languages.keys())
        self._lang_combo.addItems(list(languages.values()))
        current_idx = self._lang_codes.index(get_language()) if get_language() in self._lang_codes else 0
        self._lang_combo.setCurrentIndex(current_idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        bottom_row.addWidget(self._lang_combo)
        bottom_row.addSpacing(8)

        from utils.updater import APP_VERSION
        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet(f"color:{_C.TEXT_MUTED}; font-size:9px; font-family:'Segoe UI';")
        bottom_row.addWidget(ver)
        bottom_row.addStretch()
        ll.addLayout(bottom_row)

        card_lay.addWidget(left)

        # ═══ RIGHT PANEL (form) ═══
        right = QFrame()
        right.setFixedWidth(300)
        right.setStyleSheet("background: transparent;")

        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        self._login_form = _LoginForm()
        self._register_form = _RegisterForm()
        self._stack.addWidget(self._login_form)
        self._stack.addWidget(self._register_form)
        right_lay.addWidget(self._stack)

        # Loading bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(3)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background: transparent; border: none; }}
            QProgressBar::chunk {{ background: {_C.CYAN}; }}
        """)
        self._progress.hide()
        right_lay.addWidget(self._progress)

        card_lay.addWidget(right)

        # Close button
        close = QPushButton("✕", card)
        close.setFixedSize(28, 28)
        close.move(600 - 34, 8)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:none;
                color:{_C.TEXT_MUTED}; font-size:14px;
                font-family:'Segoe UI'; border-radius:14px;
            }}
            QPushButton:hover {{ background:#1E2A40; color:{_C.ERROR}; }}
        """)
        close.clicked.connect(_QApp.quit)

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

        # Fade in
        self._fade_in()

    # ── Drag ──────────────────────────────────────────────────

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e) -> None:
        if self._drag_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e) -> None:
        self._drag_pos = None

    # ── Fade in ───────────────────────────────────────────────

    def _fade_in(self) -> None:
        self.setWindowOpacity(0)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(300)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    # ── Language ──────────────────────────────────────────────

    def _on_language_changed(self, index: int) -> None:
        lang = self._lang_codes[index]
        set_language(lang)
        self._retranslate()

    def _retranslate(self) -> None:
        self.setWindowTitle(t("login.title"))
        self._headline.setText(t("login.headline"))
        self._description.setText(t("login.description"))
        self._login_form.retranslate()
        self._register_form.retranslate()

    # ── Handlers ─────────────────────────────────────────────

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
                api.save_session()
            else:
                settings.remove("login/remember")
                settings.remove("login/username")
                api.clear_session()
            self.login_success.emit(msg)
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
