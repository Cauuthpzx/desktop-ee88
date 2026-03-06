"""
tabs/account_tab.py — Trang tai khoan ca nhan.

Hien thi thong tin user, cho phep cap nhat email, doi mat khau,
quan ly dai ly (agent) upstream.
Uses expandable cards for compact, clean layout.
"""
from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QLabel, QComboBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QHBoxLayout, QVBoxLayout,
)
from PyQt6.QtCore import Qt

from core import theme
from core.base_widgets import BaseTab, BaseDialog, vbox, hbox, form_layout, label, divider
from core.icon import Icon, IconPath
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
    icon_hide = Icon.EYE_INVISIBLE
    icon_show = Icon.EYE
    action = line_edit.addAction(icon_hide, QLineEdit.ActionPosition.TrailingPosition)

    def toggle() -> None:
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(icon_show)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(icon_hide)

    action.triggered.connect(toggle)


# ── Agent Dialog ─────────────────────────────────────────────────

class _AgentDialog(BaseDialog):
    """Dialog to add/edit an agent."""

    def __init__(self, parent=None, data: dict | None = None):
        super().__init__(
            parent,
            title=t("account.agent_dialog_title"),
            min_width=420,
            data=data,
        )

    def _build_form(self, form) -> None:
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(t("account.agent_name"))
        form.addRow(t("account.agent_name") + ":", self._name_edit)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText(t("account.agent_username"))
        form.addRow(t("account.agent_username") + ":", self._username_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setPlaceholderText(t("account.agent_password"))
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        _add_eye_toggle(self._password_edit)
        form.addRow(t("account.agent_password") + ":", self._password_edit)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("Mặc định: https://a2u4k.ee88dly.com")
        form.addRow(t("account.agent_base_url") + ":", self._url_edit)

    def _fill(self, data: dict) -> None:
        self._name_edit.setText(data.get("name", ""))
        self._username_edit.setText(data.get("ext_username", ""))
        # Don't fill password on edit — user must re-enter
        self._url_edit.setText(data.get("base_url", ""))
        # Disable username edit on existing agent
        self._username_edit.setReadOnly(True)
        self._username_edit.setEnabled(False)

    def get_data(self) -> dict:
        return {
            "name": self._name_edit.text().strip(),
            "ext_username": self._username_edit.text().strip(),
            "ext_password": self._password_edit.text(),
            "base_url": self._url_edit.text().strip() or None,
        }


# ── Account Tab ──────────────────────────────────────────────────

class AccountTab(BaseTab):
    """Tab quan ly tai khoan: thong tin, cap nhat email, doi mat khau, dai ly, dang xuat."""

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

        # Agent card — full width below columns
        layout.addWidget(self._build_agent_card())

        # Logout
        logout_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        logout_lay.addStretch()
        self._btn_logout = QPushButton(t("account.btn_logout"))
        self._btn_logout.setIcon(Icon.LOGOUT)
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
            self._load_agents()

    # ── Card builders ─────────────────────────────────────────

    def _build_profile_card(self) -> ExpandCard:
        self._card_info = ExpandCard(
            icon=IconPath.USER,
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
            icon=IconPath.FACE_SMILE,
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
        self._btn_save_bio.setIcon(Icon.SAVE)
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
            icon=IconPath.EMAIL,
            title=t("account.update_email"),
        )

        email_w = QWidget()
        email_lay = vbox(margins=theme.MARGIN_ZERO)
        email_w.setLayout(email_lay)

        email_form = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText(t("account.email_placeholder"))
        self._email_edit.addAction(
            Icon.EMAIL,
            QLineEdit.ActionPosition.LeadingPosition,
        )
        email_form.addWidget(self._email_edit, 1)

        self._btn_save_email = QPushButton(t("account.btn_save"))
        self._btn_save_email.setIcon(Icon.SAVE)
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
            icon=IconPath.KEY,
            title=t("account.change_password"),
        )

        pwd_w = QWidget()
        pwd_lay = vbox(margins=theme.MARGIN_ZERO)
        pwd_w.setLayout(pwd_lay)

        self._current_pwd = QLineEdit()
        self._current_pwd.setPlaceholderText(t("account.current_password"))
        self._current_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._current_pwd.addAction(
            Icon.PASSWORD,
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._current_pwd)
        pwd_lay.addWidget(self._current_pwd)

        self._new_pwd = QLineEdit()
        self._new_pwd.setPlaceholderText(t("account.new_password"))
        self._new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pwd.addAction(
            Icon.KEY,
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._new_pwd)
        pwd_lay.addWidget(self._new_pwd)

        self._confirm_pwd = QLineEdit()
        self._confirm_pwd.setPlaceholderText(t("account.confirm_password"))
        self._confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pwd.addAction(
            Icon.KEY,
            QLineEdit.ActionPosition.LeadingPosition,
        )
        _add_eye_toggle(self._confirm_pwd)
        pwd_lay.addWidget(self._confirm_pwd)

        btn_pwd_lay = hbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        btn_pwd_lay.addStretch()
        self._btn_change_pwd = QPushButton(t("account.btn_change_password"))
        self._btn_change_pwd.setIcon(Icon.KEY)
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

    # ── Agent card ─────────────────────────────────────────────

    def _build_agent_card(self) -> ExpandCard:
        self._card_agent = ExpandCard(
            icon=IconPath.SUPPORT_AGENT,
            title=t("account.my_agents"),
        )

        agent_w = QWidget()
        agent_lay = vbox(margins=theme.MARGIN_ZERO)
        agent_w.setLayout(agent_lay)

        # Toolbar
        tb = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
        self._btn_add_agent = QPushButton(t("account.agent_add"))
        self._btn_add_agent.setIcon(Icon.ADD)
        self._btn_add_agent.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_add_agent.clicked.connect(self._on_add_agent)
        tb.addWidget(self._btn_add_agent)
        tb.addStretch()
        agent_lay.addLayout(tb)

        # Table
        self._agent_table = QTableWidget()
        self._agent_table.setColumnCount(6)
        self._agent_headers = [
            t("account.agent_name"),
            t("account.agent_username"),
            t("account.agent_status"),
            t("account.agent_last_login"),
            t("account.agent_base_url"),
            "",  # actions
        ]
        self._agent_table.setHorizontalHeaderLabels(self._agent_headers)
        self._agent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._agent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._agent_table.setAlternatingRowColors(True)
        self._agent_table.verticalHeader().setVisible(False)
        header = self._agent_table.horizontalHeader()
        for col in range(5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._agent_table.setColumnWidth(5, 300)
        agent_lay.addWidget(self._agent_table)

        # Message
        self._agent_msg = QLabel()
        self._agent_msg.setWordWrap(True)
        self._agent_msg.hide()
        agent_lay.addWidget(self._agent_msg)

        # Cache
        self._agents_data: list[dict] = []

        self._card_agent.add_widget(agent_w)
        return self._card_agent

    # Status color mapping
    _STATUS_COLORS = {
        "active": "#2e7d32",       # green
        "logging_in": "#f57c00",   # orange
        "error": "#d32f2f",        # red
        "offline": "#757575",      # gray
    }

    def _populate_agent_table(self) -> None:
        """Fill table from cached agents data."""
        from PyQt6.QtGui import QColor, QBrush, QFont

        table = self._agent_table
        table.setUpdatesEnabled(False)
        table.setRowCount(len(self._agents_data))
        center = Qt.AlignmentFlag.AlignCenter

        for row, ag in enumerate(self._agents_data):
            # Name
            item = QTableWidgetItem(ag.get("name", ""))
            item.setTextAlignment(center)
            item.setData(Qt.ItemDataRole.UserRole, ag.get("id"))
            table.setItem(row, 0, item)

            # Username
            item = QTableWidgetItem(ag.get("ext_username", ""))
            item.setTextAlignment(center)
            table.setItem(row, 1, item)

            # Status — colored text
            status = ag.get("status", "offline")
            status_text = t(f"account.agent_status_{status}")
            error_info = ag.get("login_error", "")
            if status == "error" and error_info:
                translated = t(error_info)
                if translated != error_info:
                    error_info = translated
                status_text = f"{status_text} ({error_info})"
            item = QTableWidgetItem(status_text)
            item.setTextAlignment(center)
            color = self._STATUS_COLORS.get(status, "#757575")
            item.setForeground(QBrush(QColor(color)))
            bold_font = QFont()
            bold_font.setBold(True)
            item.setFont(bold_font)
            table.setItem(row, 2, item)

            # Last login
            item = QTableWidgetItem(self._format_datetime(ag.get("last_login_at")))
            item.setTextAlignment(center)
            table.setItem(row, 3, item)

            # Base URL
            item = QTableWidgetItem(ag.get("base_url", ""))
            item.setTextAlignment(center)
            table.setItem(row, 4, item)

            # Action buttons
            actions_w = QWidget()
            actions_lay = QHBoxLayout(actions_w)
            actions_lay.setContentsMargins(2, 2, 2, 2)
            actions_lay.setSpacing(theme.SPACING_XS)

            agent_id = ag.get("id")

            # Login button — color based on status
            btn_login = QPushButton(t("account.agent_login"))
            btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_login.clicked.connect(lambda _, aid=agent_id: self._on_login_agent(aid))
            if status == "active":
                btn_login.setStyleSheet(
                    "QPushButton { color: #2e7d32; border: 1px solid #2e7d32; }"
                    "QPushButton:hover { background: #e8f5e9; }"
                )
                btn_login.setText(t("account.agent_login"))
            elif status == "error":
                btn_login.setStyleSheet(
                    "QPushButton { color: #d32f2f; border: 1px solid #d32f2f; }"
                    "QPushButton:hover { background: #fde8e8; }"
                )
            elif status == "logging_in":
                btn_login.setEnabled(False)
                btn_login.setText("...")
            actions_lay.addWidget(btn_login)

            # Check session button
            btn_check = QPushButton(t("account.agent_check"))
            btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_check.clicked.connect(lambda _, aid=agent_id: self._on_check_agent(aid))
            btn_check.setEnabled(status == "active")
            actions_lay.addWidget(btn_check)

            btn_edit = QPushButton(t("account.agent_edit"))
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, aid=agent_id: self._on_edit_agent(aid))
            actions_lay.addWidget(btn_edit)

            btn_del = QPushButton(t("crud.delete"))
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(lambda _, aid=agent_id: self._on_delete_agent(aid))
            actions_lay.addWidget(btn_del)

            table.setCellWidget(row, 5, actions_w)

        table.setUpdatesEnabled(True)

        count = len(self._agents_data)
        active = sum(1 for a in self._agents_data if a.get("status") == "active")
        desc = f"{count} agent{'s' if count != 1 else ''}"
        if active:
            desc += f" ({active} active)"
        self._card_agent.set_description(desc)

    # ── Agent CRUD ─────────────────────────────────────────────

    def _load_agents(self) -> None:
        run_in_thread(
            lambda: api.get("/api/agents"),
            on_result=self._on_agents_loaded,
            on_error=lambda e: logger.error("Load agents failed: %s", e),
        )

    def _on_agents_loaded(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        if ok and data.get("ok"):
            self._agents_data = data.get("agents", [])
            self._populate_agent_table()

    def _on_add_agent(self) -> None:
        dlg = _AgentDialog(self.window())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        form_data = dlg.get_data()
        errors = validate_all([
            required(t("account.agent_name"), form_data["name"]),
            required(t("account.agent_username"), form_data["ext_username"]),
        ])
        if errors:
            from dialogs.confirm_dialog import warn
            warn(self.window(), "\n".join(errors))
            return

        run_in_thread(
            lambda: api.post("/api/agents", form_data),
            on_result=self._on_agent_saved,
            on_error=lambda e: self._show_msg(self._agent_msg, str(e), error=True),
        )

    def _on_edit_agent(self, agent_id: int) -> None:
        agent = next((a for a in self._agents_data if a.get("id") == agent_id), None)
        if not agent:
            return
        dlg = _AgentDialog(self.window(), data=agent)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        form_data = dlg.get_data()
        # Only send changed fields
        update: dict = {}
        if form_data["name"] and form_data["name"] != agent.get("name"):
            update["name"] = form_data["name"]
        if form_data["ext_password"]:
            update["ext_password"] = form_data["ext_password"]
        if form_data["base_url"] != agent.get("base_url"):
            update["base_url"] = form_data["base_url"]

        if not update:
            return

        run_in_thread(
            lambda: api.put(f"/api/agents/{agent_id}", update),
            on_result=self._on_agent_saved,
            on_error=lambda e: self._show_msg(self._agent_msg, str(e), error=True),
        )

    def _on_agent_saved(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        if ok and data.get("ok"):
            self._show_msg(self._agent_msg, t("account.agent_saved"), error=False)
            self._load_agents()
        else:
            self._show_msg(self._agent_msg, data.get("message", t("api.error_generic")), error=True)

    def _on_delete_agent(self, agent_id: int) -> None:
        agent = next((a for a in self._agents_data if a.get("id") == agent_id), None)
        if not agent:
            return
        from dialogs.confirm_dialog import confirm
        name = agent.get("name", "")
        if not confirm(self.window(), t("account.agent_delete_confirm", name=name)):
            return
        run_in_thread(
            lambda: api.delete(f"/api/agents/{agent_id}"),
            on_result=lambda r: self._on_agent_deleted(r),
            on_error=lambda e: self._show_msg(self._agent_msg, str(e), error=True),
        )

    def _on_agent_deleted(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        if ok and data.get("ok"):
            self._show_msg(self._agent_msg, t("account.agent_deleted"), error=False)
            self._load_agents()
        else:
            self._show_msg(self._agent_msg, data.get("message", t("api.error_generic")), error=True)

    # ── Agent login/logout ─────────────────────────────────────

    def _on_login_agent(self, agent_id: int) -> None:
        agent = next((a for a in self._agents_data if a.get("id") == agent_id), None)
        if not agent:
            return

        if not agent.get("has_password"):
            self._show_msg(self._agent_msg, t("account.agent_no_password"), error=True)
            return

        name = agent.get("name", "")
        self._loading.start(t("account.agent_logging_in", name=name))

        run_in_thread(
            lambda: api.post(f"/api/agents/{agent_id}/login"),
            on_result=self._on_agent_login_result,
            on_error=lambda e: self._show_msg(self._agent_msg, str(e), error=True),
            on_finished=self._loading.stop,
        )

    def _on_agent_login_result(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        if ok and data.get("ok"):
            attempts = data.get("captcha_attempts", "?")
            self._show_msg(
                self._agent_msg,
                t("account.agent_login_success", n=str(attempts)),
                error=False,
            )
            self._load_agents()
        else:
            error_msg = data.get("message", t("api.error_unknown"))
            self._show_msg(
                self._agent_msg,
                t("account.agent_login_failed", error=error_msg),
                error=True,
            )
            self._load_agents()

    # ── Agent check session ───────────────────────────────────

    def _on_check_agent(self, agent_id: int) -> None:
        agent = next((a for a in self._agents_data if a.get("id") == agent_id), None)
        if not agent:
            return

        name = agent.get("name", "")
        self._show_msg(self._agent_msg, t("account.agent_checking", name=name), error=False)

        run_in_thread(
            lambda: api.post(f"/api/agents/{agent_id}/check"),
            on_result=self._on_check_result,
            on_error=lambda e: self._show_msg(self._agent_msg, str(e), error=True),
        )

    def _on_check_result(self, result: tuple[bool, dict]) -> None:
        ok, data = result
        if ok and data.get("ok"):
            self._show_msg(self._agent_msg, t("account.agent_session_valid"), error=False)
        else:
            msg = data.get("message", t("api.error_unknown"))
            self._show_msg(self._agent_msg, t("account.agent_session_expired_msg", error=msg), error=True)
        self._load_agents()

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

        # Agent card
        self._card_agent.set_title(t("account.my_agents"))
        self._btn_add_agent.setText(t("account.agent_add"))
        self._agent_table.setHorizontalHeaderLabels([
            t("account.agent_name"),
            t("account.agent_username"),
            t("account.agent_status"),
            t("account.agent_last_login"),
            t("account.agent_base_url"),
            "",
        ])
        # Re-populate to update status texts and action buttons
        if self._agents_data:
            self._populate_agent_table()

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
            self._show_msg(self._email_msg, data.get("message", t("api.error_generic")), error=True)
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
            self._show_msg(self._status_msg, data.get("message", t("api.error_generic")), error=True)

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
        # Auto-translate server i18n keys (e.g. "server.wrong_password")
        if text and "." in text:
            translated = t(text)
            if translated != text:
                text = translated
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
