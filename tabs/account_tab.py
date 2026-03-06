"""
tabs/account_tab.py — Trang tai khoan ca nhan.

Hien thi thong tin user, cho phep cap nhat email va doi mat khau.
Uses expandable cards for compact, clean layout.
"""
from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QTextEdit,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from core import theme
from core.base_widgets import BaseTab, vbox, hbox, form_layout, label, divider
from core.theme import theme_signals
from core.i18n import t
from utils.api import api
from utils.auth import auth
from utils.validators import required, min_length, email as validate_email, validate_all
from utils.thread_worker import run_in_thread
from widgets.loading import LoadingOverlay
from widgets.expand_card import ExpandCard

logger = logging.getLogger(__name__)


def _add_eye_toggle(line_edit: QLineEdit) -> None:
    """Toggle show/hide password."""
    icon_hide = QIcon("icons/layui/eye-invisible.svg")
    icon_show = QIcon("icons/layui/eye.svg")
    action = line_edit.addAction(icon_hide, QLineEdit.ActionPosition.TrailingPosition)

    def toggle() -> None:
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(icon_show)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(icon_hide)

    action.triggered.connect(toggle)


class AccountTab(BaseTab):
    """Tab quan ly tai khoan: thong tin, cap nhat email, doi mat khau, dang xuat."""

    def _build(self, layout) -> None:
        self._title_lbl = label(t("account.title"), bold=True, size=theme.FONT_SIZE_LG)
        layout.addWidget(self._title_lbl)
        layout.addWidget(divider())

        columns = hbox(spacing=theme.SPACING_LG, margins=theme.MARGIN_ZERO)

        col_left = vbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        col_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        col_right = vbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        col_right.setAlignment(Qt.AlignmentFlag.AlignTop)

        col_left.addWidget(self._build_profile_card())
        col_left.addWidget(self._build_status_card())
        col_right.addWidget(self._build_email_card())
        col_right.addWidget(self._build_password_card())

        columns.addLayout(col_left, 1)
        columns.addLayout(col_right, 1)
        layout.addLayout(columns)

        # Logout
        logout_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        logout_lay.addStretch()
        self._btn_logout = QPushButton(t("account.btn_logout"))
        self._btn_logout.setIcon(QIcon("icons/layui/logout.svg"))
        self._btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_logout.clicked.connect(self._on_logout)
        logout_lay.addWidget(self._btn_logout)
        layout.addLayout(logout_lay)

        self._apply_logout_style()
        theme_signals.changed.connect(self._on_theme_changed)

        self._loading = LoadingOverlay(self)
        self._profile_loaded = False

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._profile_loaded:
            self._profile_loaded = True
            self._load_profile()

    # ── Card builders ─────────────────────────────────────────

    def _build_profile_card(self) -> ExpandCard:
        self._card_info = ExpandCard(
            icon="icons/layui/user.svg",
            title=t("account.profile_info"),
        )

        info_form = form_layout(margins=theme.MARGIN_ZERO)

        self._lbl_username = QLabel("—")
        self._lbl_username.setFont(theme.font(bold=True))
        self._flbl_username = QLabel(t("account.username"))
        info_form.addRow(self._flbl_username, self._lbl_username)

        self._lbl_role = QLabel("—")
        self._flbl_role = QLabel(t("account.role"))
        info_form.addRow(self._flbl_role, self._lbl_role)

        self._lbl_created = QLabel("—")
        self._flbl_created = QLabel(t("account.created_at"))
        info_form.addRow(self._flbl_created, self._lbl_created)

        self._lbl_last_login = QLabel("—")
        self._flbl_last_login = QLabel(t("account.last_login"))
        info_form.addRow(self._flbl_last_login, self._lbl_last_login)

        info_w = QWidget()
        info_w.setLayout(info_form)
        self._card_info.add_widget(info_w)
        return self._card_info

    def _build_status_card(self) -> ExpandCard:
        self._card_status = ExpandCard(
            icon="icons/layui/face-smile.svg",
            title=t("account.status_section"),
        )

        status_w = QWidget()
        status_lay = vbox(margins=theme.MARGIN_ZERO)
        status_w.setLayout(status_lay)

        presence_row = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        self._lbl_presence = label(t("account.presence"))
        presence_row.addWidget(self._lbl_presence)
        self._presence_combo = QComboBox()
        self._presence_keys = ["online", "busy", "away", "dnd", "invisible"]
        self._presence_combo.addItems([
            t("account.presence_online"),
            t("account.presence_busy"),
            t("account.presence_away"),
            t("account.presence_dnd"),
            t("account.presence_invisible"),
        ])
        self._presence_combo.currentIndexChanged.connect(self._on_presence_changed)
        presence_row.addWidget(self._presence_combo, 1)
        status_lay.addLayout(presence_row)

        self._lbl_bio = label(t("account.bio_label"))
        status_lay.addWidget(self._lbl_bio)
        self._bio_edit = QTextEdit()
        self._bio_edit.setPlaceholderText(t("account.bio_placeholder"))
        self._bio_edit.setMaximumHeight(80)
        status_lay.addWidget(self._bio_edit)

        bio_btn_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        bio_btn_lay.addStretch()
        self._btn_save_bio = QPushButton(t("account.btn_save_bio"))
        self._btn_save_bio.setIcon(QIcon("icons/layui/ok-circle.svg"))
        self._btn_save_bio.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_save_bio.clicked.connect(self._on_save_bio)
        bio_btn_lay.addWidget(self._btn_save_bio)
        status_lay.addLayout(bio_btn_lay)

        self._status_msg = QLabel()
        self._status_msg.setWordWrap(True)
        self._status_msg.hide()
        status_lay.addWidget(self._status_msg)

        self._card_status.add_widget(status_w)
        return self._card_status

    def _build_email_card(self) -> ExpandCard:
        self._card_email = ExpandCard(
            icon="icons/layui/email.svg",
            title=t("account.update_email"),
        )

        email_w = QWidget()
        email_lay = vbox(margins=theme.MARGIN_ZERO)
        email_w.setLayout(email_lay)

        email_form = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText(t("account.email_placeholder"))
        self._email_edit.addAction(
            QIcon("icons/layui/email.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        email_form.addWidget(self._email_edit, 1)

        self._btn_save_email = QPushButton(t("account.btn_save"))
        self._btn_save_email.setIcon(QIcon("icons/layui/ok-circle.svg"))
        self._btn_save_email.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_save_email.clicked.connect(self._on_save_email)
        email_form.addWidget(self._btn_save_email)
        email_lay.addLayout(email_form)

        self._email_msg = QLabel()
        self._email_msg.setWordWrap(True)
        self._email_msg.hide()
        email_lay.addWidget(self._email_msg)

        self._card_email.add_widget(email_w)
        return self._card_email

    def _build_password_card(self) -> ExpandCard:
        self._card_pwd = ExpandCard(
            icon="icons/layui/key.svg",
            title=t("account.change_password"),
        )

        pwd_w = QWidget()
        pwd_lay = vbox(margins=theme.MARGIN_ZERO)
        pwd_w.setLayout(pwd_lay)

        self._current_pwd = QLineEdit()
        self._current_pwd.setPlaceholderText(t("account.current_password"))
        self._current_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._current_pwd.addAction(
            QIcon("icons/layui/password.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._current_pwd)
        pwd_lay.addWidget(self._current_pwd)

        self._new_pwd = QLineEdit()
        self._new_pwd.setPlaceholderText(t("account.new_password"))
        self._new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pwd.addAction(
            QIcon("icons/layui/key.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._new_pwd)
        pwd_lay.addWidget(self._new_pwd)

        self._confirm_pwd = QLineEdit()
        self._confirm_pwd.setPlaceholderText(t("account.confirm_password"))
        self._confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pwd.addAction(
            QIcon("icons/layui/key.svg"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._confirm_pwd)
        pwd_lay.addWidget(self._confirm_pwd)

        btn_pwd_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        btn_pwd_lay.addStretch()
        self._btn_change_pwd = QPushButton(t("account.btn_change_password"))
        self._btn_change_pwd.setIcon(QIcon("icons/layui/key.svg"))
        self._btn_change_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_change_pwd.clicked.connect(self._on_change_password)
        btn_pwd_lay.addWidget(self._btn_change_pwd)
        pwd_lay.addLayout(btn_pwd_lay)

        self._pwd_msg = QLabel()
        self._pwd_msg.setWordWrap(True)
        self._pwd_msg.hide()
        pwd_lay.addWidget(self._pwd_msg)

        self._card_pwd.add_widget(pwd_w)
        return self._card_pwd

    # ── Theme ─────────────────────────────────────────────────

    def _apply_logout_style(self) -> None:
        if theme.is_dark():
            self._btn_logout.setStyleSheet(
                "QPushButton { color: #ef5350; } "
                "QPushButton:hover { color: #ff867c; }"
            )
        else:
            self._btn_logout.setStyleSheet(
                "QPushButton { color: #d32f2f; } "
                "QPushButton:hover { color: #b71c1c; }"
            )

    def _on_theme_changed(self, _dark: bool) -> None:
        self._apply_logout_style()

    # ── Retranslate ───────────────────────────────────────────

    def retranslate(self) -> None:
        self._title_lbl.setText(t("account.title"))
        self._card_info.set_title(t("account.profile_info"))
        self._flbl_username.setText(t("account.username"))
        self._flbl_role.setText(t("account.role"))
        self._flbl_created.setText(t("account.created_at"))
        self._flbl_last_login.setText(t("account.last_login"))
        self._card_status.set_title(t("account.status_section"))
        self._lbl_presence.setText(t("account.presence"))
        self._presence_combo.blockSignals(True)
        idx = self._presence_combo.currentIndex()
        self._presence_combo.clear()
        self._presence_combo.addItems([
            t("account.presence_online"),
            t("account.presence_busy"),
            t("account.presence_away"),
            t("account.presence_dnd"),
            t("account.presence_invisible"),
        ])
        self._presence_combo.setCurrentIndex(idx)
        self._presence_combo.blockSignals(False)
        self._lbl_bio.setText(t("account.bio_label"))
        self._bio_edit.setPlaceholderText(t("account.bio_placeholder"))
        self._btn_save_bio.setText(t("account.btn_save_bio"))
        self._card_email.set_title(t("account.update_email"))
        self._email_edit.setPlaceholderText(t("account.email_placeholder"))
        self._btn_save_email.setText(t("account.btn_save"))
        self._card_pwd.set_title(t("account.change_password"))
        self._current_pwd.setPlaceholderText(t("account.current_password"))
        self._new_pwd.setPlaceholderText(t("account.new_password"))
        self._confirm_pwd.setPlaceholderText(t("account.confirm_password"))
        self._btn_change_pwd.setText(t("account.btn_change_password"))
        self._btn_logout.setText(t("account.btn_logout"))

    # ── Load profile ──────────────────────────────────────────

    def _load_profile(self) -> None:
        self._loading.start(t("loading.loading"))
        run_in_thread(
            lambda: api.get("/api/me"),
            on_result=self._on_profile_loaded,
            on_error=self._on_profile_error,
            on_finished=self._loading.stop,
        )

    def _on_profile_loaded(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        if not ok:
            self._show_msg(self._email_msg, data.get("message", "Error"), error=True)
            return

        username = data.get("username", "—")
        role_str = self._format_role(data.get("role", "user"))

        self._lbl_username.setText(username)
        self._lbl_role.setText(role_str)
        self._lbl_created.setText(self._format_datetime(data.get("created_at")))
        self._lbl_last_login.setText(self._format_datetime(data.get("last_login_at")))
        self._card_info.set_description(f"{username} ({role_str})")

        email_val = data.get("email", "")
        self._email_edit.setText(email_val)
        self._card_email.set_description(email_val or "—")

        presence = data.get("presence", "online")
        if presence in self._presence_keys:
            self._presence_combo.blockSignals(True)
            self._presence_combo.setCurrentIndex(self._presence_keys.index(presence))
            self._presence_combo.blockSignals(False)
            self._card_status.set_description(self._presence_combo.currentText())

        self._bio_edit.setPlainText(data.get("bio", ""))

    def _on_profile_error(self, err: str) -> None:
        logger.error("Load profile failed: %s", err)
        self._show_msg(self._email_msg, t("account.error_load"), error=True)

    # ── Presence & Bio ────────────────────────────────────────

    def _on_presence_changed(self, index: int) -> None:
        presence = self._presence_keys[index]
        self._card_status.set_description(self._presence_combo.currentText())
        run_in_thread(
            lambda: api.put("/api/me", {"presence": presence}),
            on_result=lambda r: self._on_status_result(r, "presence"),
            on_error=lambda e: self._show_msg(self._status_msg, str(e), error=True),
        )

    def _on_save_bio(self) -> None:
        bio = self._bio_edit.toPlainText().strip()[:500]
        self._btn_save_bio.setEnabled(False)
        run_in_thread(
            lambda: api.put("/api/me", {"bio": bio}),
            on_result=lambda r: self._on_status_result(r, "bio"),
            on_error=lambda e: self._show_msg(self._status_msg, str(e), error=True),
            on_finished=lambda: self._btn_save_bio.setEnabled(True),
        )

    def _on_status_result(self, result: tuple[bool, dict], field: str) -> None:
        ok, data = result
        if ok and data.get("ok", False):
            self._show_msg(self._status_msg, t("account.status_saved"), error=False)
        else:
            self._show_msg(self._status_msg, data.get("message", "Error"), error=True)

    # ── Save email ────────────────────────────────────────────

    def _on_save_email(self) -> None:
        email_val = self._email_edit.text().strip()
        if email_val:
            errors = validate_all([validate_email(t("account.email_label"), email_val)])
            if errors:
                self._show_msg(self._email_msg, "\n".join(errors), error=True)
                return

        self._email_msg.hide()
        self._btn_save_email.setEnabled(False)
        run_in_thread(
            lambda: api.put("/api/me", {"email": email_val or None}),
            on_result=self._on_email_saved,
            on_error=lambda e: self._show_msg(self._email_msg, str(e), error=True),
            on_finished=lambda: self._btn_save_email.setEnabled(True),
        )

    def _on_email_saved(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        msg = data.get("message", "")
        if ok and data.get("ok", False):
            self._show_msg(self._email_msg, t("account.email_saved"), error=False)
            self._card_email.set_description(self._email_edit.text().strip() or "—")
        else:
            self._show_msg(self._email_msg, msg or t("account.error_save"), error=True)

    # ── Change password ───────────────────────────────────────

    def _on_change_password(self) -> None:
        current = self._current_pwd.text()
        new_pwd = self._new_pwd.text()
        confirm = self._confirm_pwd.text()

        errors = validate_all([
            required(t("account.current_password"), current),
            required(t("account.new_password"), new_pwd),
            min_length(t("account.new_password"), new_pwd, 6),
            required(t("account.confirm_password"), confirm),
        ])

        if not errors and new_pwd != confirm:
            errors.append(t("account.password_mismatch"))

        if errors:
            self._show_msg(self._pwd_msg, "\n".join(errors), error=True)
            return

        self._pwd_msg.hide()
        self._btn_change_pwd.setEnabled(False)
        run_in_thread(
            lambda: api.put("/api/me/password", {
                "current_password": current,
                "new_password": new_pwd,
            }),
            on_result=self._on_password_changed,
            on_error=lambda e: self._show_msg(self._pwd_msg, str(e), error=True),
            on_finished=lambda: self._btn_change_pwd.setEnabled(True),
        )

    def _on_password_changed(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        msg = data.get("message", "")
        if ok and data.get("ok", False):
            self._current_pwd.clear()
            self._new_pwd.clear()
            self._confirm_pwd.clear()
            self._show_msg(self._pwd_msg, t("account.password_changed"), error=False)
        else:
            self._show_msg(self._pwd_msg, msg or t("account.error_change_pwd"), error=True)

    # ── Logout ────────────────────────────────────────────────

    def _on_logout(self) -> None:
        from dialogs.confirm_dialog import confirm
        if not confirm(self.window(), t("account.confirm_logout")):
            return
        self._profile_loaded = False
        auth.logout()

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _show_msg(lbl: QLabel, text: str, error: bool = True) -> None:
        color = "#d32f2f" if error else "#2e7d32"
        bg = "#fde8e8" if error else "#e8f5e9"
        lbl.setStyleSheet(f"color: {color}; background: {bg}; padding: 6px; border-radius: 4px;")
        lbl.setText(text)
        lbl.show()

    @staticmethod
    def _format_role(role: str) -> str:
        roles = {"admin": "Administrator", "user": "User", "moderator": "Moderator"}
        return roles.get(role, role.capitalize())

    @staticmethod
    def _format_datetime(dt_str: str | None) -> str:
        if not dt_str:
            return "—"
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return dt_str
