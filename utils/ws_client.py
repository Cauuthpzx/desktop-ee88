"""
utils/ws_client.py — WebSocket client cho PyQt6.

Dung QWebSocket (built-in PyQt6) — khong can them dependency.

Usage:
    from utils.ws_client import ws_client

    # Ket noi (goi sau khi login thanh cong):
    ws_client.connect()

    # Lang nghe events:
    ws_client.data_updated.connect(self._on_data_updated)
    ws_client.member_added.connect(self._on_member_added)
    ws_client.member_removed.connect(self._on_member_removed)
    ws_client.presence_changed.connect(self._on_presence)

    # Ngat ket noi (goi khi logout):
    ws_client.disconnect()
"""
from __future__ import annotations

import json
import logging

from PyQt6.QtCore import QObject, QUrl, QTimer, pyqtSignal
from PyQt6.QtWebSockets import QWebSocket

logger = logging.getLogger(__name__)


class WsClient(QObject):
    """WebSocket client — auto reconnect, heartbeat, typed signals."""

    # -- Signals ------------------------------------------------------------
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    # Group events
    data_updated = pyqtSignal(dict)        # {group_id, data_type, version, synced_by}
    member_added = pyqtSignal(dict)        # {group_id, agent_name, added_by}
    member_removed = pyqtSignal(dict)      # {group_id, agent_id}
    presence_changed = pyqtSignal(dict)    # {group_id, online: [...], count}
    group_updated = pyqtSignal(dict)       # {group_id, ...}
    permissions_changed = pyqtSignal(dict) # {group_id, agent_id, ...}

    # Generic
    message_received = pyqtSignal(dict)    # Moi message (fallback)

    # -- Config -------------------------------------------------------------
    RECONNECT_INTERVALS = [1, 2, 5, 10, 30, 60]  # seconds, escalating backoff
    MAX_RECONNECT_ATTEMPTS = 20  # stop after 20 attempts
    HEARTBEAT_TIMEOUT = 45  # seconds

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._ws: QWebSocket | None = None

        self._server_url: str = ""
        self._token: str = ""
        self._is_connected = False
        self._should_reconnect = False
        self._reconnect_attempt = 0

        # Reconnect timer
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._do_reconnect)

        # Heartbeat timeout timer
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(self.HEARTBEAT_TIMEOUT * 1000)
        self._heartbeat_timer.timeout.connect(self._on_heartbeat_timeout)

    # -- Public API ---------------------------------------------------------

    def connect(self, server_url: str | None = None, token: str | None = None) -> None:
        """Ket noi WebSocket server."""
        if server_url:
            self._server_url = server_url
        if token:
            self._token = token

        if not self._server_url or not self._token:
            from utils.api import api
            import os
            from dotenv import load_dotenv
            load_dotenv()
            self._server_url = os.getenv("API_URL", "http://localhost:8000")
            self._token = api.token or ""

        if not self._token:
            logger.warning("WS: No token, skip connect")
            return

        self._should_reconnect = True
        self._reconnect_attempt = 0
        self._do_connect()

    def disconnect(self) -> None:
        """Ngat ket noi va khong reconnect."""
        self._should_reconnect = False
        self._reconnect_timer.stop()
        self._heartbeat_timer.stop()
        self._cleanup_ws()
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def join_room(self, group_id: int) -> None:
        """Join vao room nhom (khi mo tab nhom)."""
        self._send({"type": "join_room", "group_id": group_id})

    def leave_room(self, group_id: int) -> None:
        """Roi room nhom (khi dong tab nhom)."""
        self._send({"type": "leave_room", "group_id": group_id})

    # -- Internal -----------------------------------------------------------

    def _create_ws(self) -> None:
        """Tao QWebSocket moi — phai tao lai moi lan connect de tranh nullptr."""
        self._cleanup_ws()
        self._ws = QWebSocket("", parent=self)
        self._ws.connected.connect(self._on_connected)
        self._ws.disconnected.connect(self._on_disconnected)
        self._ws.textMessageReceived.connect(self._on_message)
        self._ws.errorOccurred.connect(self._on_error)

    def _cleanup_ws(self) -> None:
        """Huy QWebSocket cu an toan."""
        if self._ws is not None:
            ws = self._ws
            self._ws = None
            # Block signals first — prevents callbacks during teardown
            try:
                ws.blockSignals(True)
            except RuntimeError:
                return
            # Don't call disconnect() after blockSignals — it causes
            # "wildcard call disconnects from destroyed signal" warnings.
            # blockSignals(True) + deleteLater() is sufficient.
            try:
                if ws.isValid():
                    ws.close()
            except RuntimeError:
                pass
            ws.deleteLater()

    def _do_connect(self) -> None:
        """Thuc hien ket noi."""
        # Tao QWebSocket moi moi lan connect
        self._create_ws()

        # Convert http:// -> ws://, https:// -> wss://
        ws_url = self._server_url.replace("https://", "wss://").replace(
            "http://", "ws://")
        ws_url = f"{ws_url}/ws?token={self._token}"

        logger.info("WS connecting to %s...", ws_url.split("?")[0])
        self._ws.open(QUrl(ws_url))

    def _do_reconnect(self) -> None:
        """Reconnect voi backoff."""
        if not self._should_reconnect:
            return
        logger.info("WS reconnecting (attempt %d)...", self._reconnect_attempt + 1)
        self._do_connect()

    def _schedule_reconnect(self) -> None:
        """Len lich reconnect voi escalating backoff."""
        if not self._should_reconnect:
            return
        if self._reconnect_attempt >= self.MAX_RECONNECT_ATTEMPTS:
            logger.warning("WS max reconnect attempts reached, giving up")
            self._should_reconnect = False
            return
        idx = min(self._reconnect_attempt, len(self.RECONNECT_INTERVALS) - 1)
        delay = self.RECONNECT_INTERVALS[idx] * 1000
        self._reconnect_attempt += 1
        logger.info(
            "WS reconnect in %ds (attempt %d/%d)",
            delay // 1000, self._reconnect_attempt, self.MAX_RECONNECT_ATTEMPTS,
        )
        self._reconnect_timer.start(delay)

    def _send(self, data: dict) -> None:
        """Gui JSON message."""
        if self._is_connected and self._ws and self._ws.isValid():
            self._ws.sendTextMessage(json.dumps(data))

    # -- Signal handlers ----------------------------------------------------

    def _on_connected(self) -> None:
        self._is_connected = True
        self._reconnect_attempt = 0
        self._heartbeat_timer.start()
        logger.info("WS connected!")
        self.connected.emit()

    def _on_disconnected(self) -> None:
        was_connected = self._is_connected
        self._is_connected = False
        self._heartbeat_timer.stop()
        if was_connected:
            logger.info("WS disconnected")
            self.disconnected.emit()
        self._schedule_reconnect()

    def _on_error(self, err) -> None:
        logger.error("WS error: %s", err)

    def _on_heartbeat_timeout(self) -> None:
        """Server khong ping trong 45s -> connection chet -> reconnect."""
        logger.warning("WS heartbeat timeout, reconnecting...")
        if self._ws and self._ws.isValid():
            self._ws.close()

    def _on_message(self, raw: str) -> None:
        """Xu ly message tu server."""
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = msg.get("type", "")

        # Reset heartbeat timer (server con song)
        self._heartbeat_timer.start()

        # Route to typed signals
        if msg_type == "ping":
            self._send({"type": "pong"})

        elif msg_type == "data_updated":
            self.data_updated.emit(msg)

        elif msg_type == "member_added":
            self.member_added.emit(msg)

        elif msg_type == "member_removed":
            self.member_removed.emit(msg)

        elif msg_type == "presence":
            self.presence_changed.emit(msg)

        elif msg_type == "group_updated":
            self.group_updated.emit(msg)

        elif msg_type == "permissions_changed":
            self.permissions_changed.emit(msg)

        # Emit generic signal cho tat ca
        self.message_received.emit(msg)


# Singleton
ws_client = WsClient()
