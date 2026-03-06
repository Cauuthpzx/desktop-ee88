"""
utils/auth.py
Xac thuc nguoi dung qua API server.

Dung:
    from utils.auth import auth

    auth.init()                              # health check server
    ok, msg = auth.register("admin", "123456")
    ok, msg = auth.login("admin", "123456")
"""
from __future__ import annotations

import logging

from PyQt6.QtCore import QObject, pyqtSignal

from utils.api import api

logger = logging.getLogger(__name__)


class AuthService(QObject):
    """Auth service with logout signal for UI navigation."""
    logged_out = pyqtSignal()
    def init(self) -> None:
        """Health check server khi khoi dong app."""
        if not api.health():
            logger.warning("API server khong phan hoi.")

    def register(self, username: str, password: str) -> tuple[bool, str]:
        """Dang ky tai khoan moi. Tra ve (success, message)."""
        return api.register(username, password)

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Dang nhap. Tra ve (success, username_or_message)."""
        return api.login(username, password)

    def logout(self) -> None:
        """Xoa token local va emit signal de UI quay ve login."""
        api.logout()
        self.logged_out.emit()

    @property
    def is_logged_in(self) -> bool:
        return api.is_logged_in

    @property
    def username(self) -> str | None:
        return api.username

    @property
    def role(self) -> str | None:
        return api.role

    @property
    def token(self) -> str | None:
        return api.token


# Singleton
auth = AuthService()
