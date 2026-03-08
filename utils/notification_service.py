"""
utils/notification_service.py — Singleton dịch vụ thông báo.

Thu thập sự kiện từ các nguồn (WebSocket, updater, health checker, agent login)
và đẩy vào NotificationBell.

Dùng:
    from utils.notification_service import notif_service

    notif_service.bind(bell)     # bind với NotificationBell (trong app_window)
    notif_service.connect_all()  # connect tất cả signal sources
    notif_service.disconnect_all()  # cleanup khi đóng app

    # Gửi thông báo thủ công:
    notif_service.push("Tin nhắn", category="system")
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal

from core.i18n import t

if TYPE_CHECKING:
    from widgets.notification_bell import NotificationBell

logger = logging.getLogger(__name__)

# Category constants — re-export for convenience
SYSTEM = "system"
CUSTOMER = "customer"
AGENT = "agent"
GROUP = "group"


class NotificationService(QObject):
    """Singleton thu thập sự kiện → đẩy vào NotificationBell."""

    # Signal cho code bên ngoài muốn listen
    notification_added = pyqtSignal(str, str, str)  # message, category, icon

    def __init__(self) -> None:
        super().__init__()
        self._bell: NotificationBell | None = None
        self._connected = False

    def bind(self, bell: NotificationBell) -> None:
        """Gắn với NotificationBell instance."""
        self._bell = bell

    def push(self, message: str, *, category: str = SYSTEM, icon: str = "") -> None:
        """Đẩy 1 thông báo vào bell."""
        if self._bell:
            self._bell.add_notification(message, category=category, icon=icon)
        self.notification_added.emit(message, category, icon)
        logger.debug("Notification [%s]: %s", category, message)

    # ── Connect all sources ──────────────────────────────────

    def connect_all(self) -> None:
        """Connect tất cả signal sources."""
        if self._connected:
            return
        self._connected = True

        # WebSocket events
        try:
            from utils.ws_client import ws_client
            ws_client.connected.connect(self._on_ws_connected)
            ws_client.disconnected.connect(self._on_ws_disconnected)
            ws_client.member_added.connect(self._on_member_added)
            ws_client.member_removed.connect(self._on_member_removed)
            ws_client.data_updated.connect(self._on_data_synced)
        except Exception:
            logger.debug("WS signals not available")

    def disconnect_all(self) -> None:
        """Disconnect tất cả signals."""
        if not self._connected:
            return
        self._connected = False

        try:
            from utils.ws_client import ws_client
            ws_client.connected.disconnect(self._on_ws_connected)
            ws_client.disconnected.disconnect(self._on_ws_disconnected)
            ws_client.member_added.disconnect(self._on_member_added)
            ws_client.member_removed.disconnect(self._on_member_removed)
            ws_client.data_updated.disconnect(self._on_data_synced)
        except (TypeError, RuntimeError):
            pass

    # ── Event handlers ───────────────────────────────────────

    def _on_ws_connected(self) -> None:
        self.push(
            t("notification.system_connected"),
            category=SYSTEM,
            icon="icons/material/wifi.svg",
        )

    def _on_ws_disconnected(self) -> None:
        self.push(
            t("notification.system_disconnected"),
            category=SYSTEM,
            icon="icons/material/wifi_off.svg",
        )

    def _on_member_added(self, event: dict) -> None:
        name = event.get("agent_name", "")
        added_by = event.get("added_by", "")
        msg = t("notification.group_member_joined", username=added_by or name)
        self.push(msg, category=GROUP, icon="icons/material/person_add.svg")

    def _on_member_removed(self, event: dict) -> None:
        agent_id = event.get("agent_id", "")
        msg = t("notification.group_member_left", username=str(agent_id))
        self.push(msg, category=GROUP, icon="icons/material/person_remove.svg")

    def _on_data_synced(self, event: dict) -> None:
        from utils.api import api
        synced_by = event.get("synced_by", "")
        if synced_by == api.username:
            return  # Ignore own syncs
        self.push(
            t("notification.group_data_synced"),
            category=GROUP,
            icon="icons/material/sync.svg",
        )

    # ── Manual push helpers (called from other modules) ──────

    def notify_update_available(self, version: str) -> None:
        self.push(
            t("notification.system_update_available", version=version),
            category=SYSTEM,
            icon="icons/material/browser_updated.svg",
        )

    def notify_update_ready(self) -> None:
        self.push(
            t("notification.system_update_ready"),
            category=SYSTEM,
            icon="icons/material/browser_updated.svg",
        )

    def notify_health_warning(self, warning: str) -> None:
        self.push(
            t("notification.system_health_warning", warning=warning),
            category=SYSTEM,
            icon="icons/layui/warning.svg",
        )

    def notify_health_critical(self, warning: str) -> None:
        self.push(
            t("notification.system_health_critical", warning=warning),
            category=SYSTEM,
            icon="icons/layui/close-fill.svg",
        )

    def notify_agent_login_ok(self, name: str) -> None:
        self.push(
            t("notification.agent_login_ok", name=name),
            category=AGENT,
            icon="icons/material/support_agent.svg",
        )

    def notify_agent_login_fail(self, name: str) -> None:
        self.push(
            t("notification.agent_login_fail", name=name),
            category=AGENT,
            icon="icons/layui/close-fill.svg",
        )

    def notify_agent_session_expired(self, name: str) -> None:
        self.push(
            t("notification.agent_session_expired", name=name),
            category=AGENT,
            icon="icons/layui/warning.svg",
        )

    def notify_agent_relogin_ok(self, name: str) -> None:
        self.push(
            t("notification.agent_relogin_ok", name=name),
            category=AGENT,
            icon="icons/material/support_agent.svg",
        )

    def notify_customer_deposit(self, username: str, amount: str) -> None:
        self.push(
            t("notification.customer_deposit", username=username, amount=amount),
            category=CUSTOMER,
            icon="icons/material/savings.svg",
        )

    def notify_customer_withdraw(self, username: str, amount: str) -> None:
        self.push(
            t("notification.customer_withdraw", username=username, amount=amount),
            category=CUSTOMER,
            icon="icons/material/money_off.svg",
        )

    def notify_customer_new(self, username: str) -> None:
        self.push(
            t("notification.customer_new", username=username),
            category=CUSTOMER,
            icon="icons/material/person_add.svg",
        )


# Singleton
notif_service = NotificationService()
