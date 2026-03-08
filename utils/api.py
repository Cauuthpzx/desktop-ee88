"""
utils/api.py
HTTP client goi API server.

Dung:
    from utils.api import api

    # Auth
    ok, data = api.register("admin", "123456")
    ok, data = api.login("admin", "123456")
    ok, data = api.me()

    # Generic
    ok, data = api.get("/api/users")
    ok, data = api.post("/api/users", {"name": "Alice"})
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
import urllib.request
import urllib.error

from dotenv import load_dotenv
from PyQt6.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG

from core.i18n import t

# Tim .env ca khi chay tu PyInstaller bundle
if getattr(sys, "frozen", False):
    # PyInstaller --onedir: data nam trong _MEIPASS (_internal/)
    _base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_base_dir, ".env"))

logger = logging.getLogger(__name__)


class _ApiSignals(QObject):
    """Signals cho ApiClient — phai la QObject de emit tu worker thread."""
    session_expired = pyqtSignal()  # 401 + refresh fail → force logout


class ApiClient:
    """HTTP client ket noi API server."""

    def __init__(self) -> None:
        self._base = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
        self._token: str | None = None
        self._username: str | None = None
        self._role: str | None = None
        self._lock = threading.Lock()  # AUDIT-FIX: protect token state
        self._signals: _ApiSignals | None = None
        self._session_expired_fired = False  # tranh emit nhieu lan

    def init_signals(self) -> None:
        """Khoi tao signals — goi sau khi QApplication da tao."""
        self._signals = _ApiSignals()

    @property
    def session_expired(self):
        """Signal emitted khi token het han va refresh fail."""
        return self._signals.session_expired if self._signals else None

    # ── Token persistence ───────────────────────────────────
    def save_session(self) -> None:
        """Luu token vao QSettings — goi truoc khi restart de update."""
        from utils.settings import settings
        if self._token:
            settings.set("session/token", self._token)
            settings.set("session/username", self._username or "")
            settings.set("session/role", self._role or "")
        else:
            settings.remove("session/token")
            settings.remove("session/username")
            settings.remove("session/role")

    def restore_session(self) -> bool:
        """Doc token tu QSettings. Tra ve True neu token con hop le."""
        from utils.settings import settings
        token = settings.get_str("session/token")
        if not token:
            return False
        with self._lock:  # AUDIT-FIX: thread-safe token mutation
            self._token = token
            self._username = settings.get_str("session/username")
            self._role = settings.get_str("session/role")
        # Verify token still valid
        ok, data = self.me()
        if not ok:
            self.logout()
            return False
        with self._lock:
            self._username = data.get("username", self._username)
            self._role = data.get("role", self._role)
        return True

    def clear_session(self) -> None:
        """Xoa token khoi QSettings."""
        from utils.settings import settings
        settings.remove("session/token")
        settings.remove("session/username")
        settings.remove("session/role")

    # ── Properties ──────────────────────────────────────────
    @property
    def token(self) -> str | None:
        return self._token

    @property
    def username(self) -> str | None:
        return self._username

    @property
    def role(self) -> str | None:
        return self._role

    @property
    def is_logged_in(self) -> bool:
        return self._token is not None

    # ── HTTP helpers ────────────────────────────────────────
    def _raw_request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        auth: bool = True,
        timeout: int = 15,
    ) -> tuple[bool, dict]:
        """
        Goi API (khong auto-refresh). Tra ve (ok, data_dict).
        Neu loi mang/server → (False, {"message": "..."})
        """
        url = self._base + path
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode())
            return True, result
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read().decode())
            except (json.JSONDecodeError, ValueError):
                detail = {"message": f"HTTP {e.code}"}
            detail["_http_code"] = e.code
            logger.error("API %s %s → %s: %s", method, path, e.code, detail)
            return False, detail
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            logger.error("API %s %s → network error: %s", method, path, e)
            return False, {"message": t("api.error_connect")}

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        auth: bool = True,
        timeout: int = 15,
    ) -> tuple[bool, dict]:
        """Goi API voi auto-refresh token khi nhan 401."""
        ok, data = self._raw_request(method, path, body, auth, timeout)
        if ok:
            return ok, data

        # Nhan 401 + co token → thu refresh token
        http_code = data.get("_http_code", 0)
        if http_code == 401 and self._token and path != "/api/refresh":
            logger.info("Got 401 on %s, attempting token refresh...", path)
            if self._try_refresh():
                # Retry request voi token moi
                return self._raw_request(method, path, body, auth, timeout)
            # Refresh fail → session het han, force logout
            self._emit_session_expired()
        return ok, data

    def _emit_session_expired(self) -> None:
        """Emit session_expired signal (thread-safe, chi emit 1 lan)."""
        if self._session_expired_fired or not self._signals:
            return
        self._session_expired_fired = True
        logger.warning("Session expired — forcing logout")
        # Emit trong main thread (co the goi tu worker thread)
        QMetaObject.invokeMethod(
            self._signals, "session_expired",
            Qt.ConnectionType.QueuedConnection,
        )

    def _try_refresh(self) -> bool:
        """Thu gia han JWT token. Tra ve True neu thanh cong."""
        ok, data = self._raw_request("POST", "/api/refresh")
        if ok and data.get("ok"):
            with self._lock:  # AUDIT-FIX: thread-safe token mutation
                self._token = data.get("token", self._token)
                self._username = data.get("username", self._username)
                self._role = data.get("role", self._role)
            self.save_session()
            logger.info("Token refreshed successfully for %s", self._username)
            return True
        logger.warning("Token refresh failed: %s", data)
        return False

    def get(self, path: str, **kw) -> tuple[bool, dict]:
        return self._request("GET", path, **kw)

    def post(self, path: str, body: dict | None = None, **kw) -> tuple[bool, dict]:
        return self._request("POST", path, body=body, **kw)

    def put(self, path: str, body: dict | None = None, **kw) -> tuple[bool, dict]:
        return self._request("PUT", path, body=body, **kw)

    def delete(self, path: str, **kw) -> tuple[bool, dict]:
        return self._request("DELETE", path, **kw)

    # ── Auth endpoints ──────────────────────────────────────
    def register(self, username: str, password: str) -> tuple[bool, str]:
        """Dang ky. Tra ve (ok, message)."""
        ok, data = self.post("/api/register", {"username": username, "password": password}, auth=False)
        msg = data.get("message", t("api.error_unknown"))
        return data.get("ok", False), msg

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Dang nhap. Tra ve (ok, message). Neu ok, luu token."""
        ok, data = self.post("/api/login", {"username": username, "password": password}, auth=False)
        if data.get("ok"):
            with self._lock:  # AUDIT-FIX: thread-safe token mutation
                self._token = data.get("token")
                self._username = data.get("username")
                self._role = data.get("role")
                self._session_expired_fired = False  # reset khi login lai
            return True, data.get("username", "")
        return False, data.get("message", t("api.error_login"))

    def logout(self) -> None:
        """Xoa token local + QSettings."""
        with self._lock:  # AUDIT-FIX: thread-safe token mutation
            self._token = None
            self._username = None
            self._role = None
        self.clear_session()

    def me(self) -> tuple[bool, dict]:
        """Kiem tra token con hop le."""
        return self.get("/api/me")

    def health(self) -> bool:
        """Kiem tra server."""
        ok, _ = self.get("/api/health", auth=False)
        return ok


# Singleton
api = ApiClient()
