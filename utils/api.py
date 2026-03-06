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
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ApiClient:
    """HTTP client ket noi API server."""

    def __init__(self) -> None:
        self._base = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
        self._token: str | None = None
        self._username: str | None = None
        self._role: str | None = None

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
        self._token = token
        self._username = settings.get_str("session/username")
        self._role = settings.get_str("session/role")
        # Verify token still valid
        ok, data = self.me()
        if not ok:
            self.logout()
            return False
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
    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        auth: bool = True,
        timeout: int = 15,
    ) -> tuple[bool, dict]:
        """
        Goi API. Tra ve (ok, data_dict).
        Neu loi mang/server → (False, {"message": "..."})
        """
        url = self._base + path
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            result = json.loads(resp.read().decode())
            return True, result
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read().decode())
            except Exception:
                detail = {"message": f"HTTP {e.code}"}
            logger.error("API %s %s → %s: %s", method, path, e.code, detail)
            return False, detail
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            logger.error("API %s %s → network error: %s", method, path, e)
            return False, {"message": "Khong the ket noi may chu."}

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
        msg = data.get("message", "Loi khong xac dinh.")
        return data.get("ok", False), msg

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Dang nhap. Tra ve (ok, message). Neu ok, luu token."""
        ok, data = self.post("/api/login", {"username": username, "password": password}, auth=False)
        if data.get("ok"):
            self._token = data.get("token")
            self._username = data.get("username")
            self._role = data.get("role")
            return True, data.get("username", "")
        return False, data.get("message", "Loi dang nhap.")

    def logout(self) -> None:
        """Xoa token local + QSettings."""
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
