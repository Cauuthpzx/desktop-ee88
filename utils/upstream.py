"""
utils/upstream.py — Upstream EE88 client (local-first, toi uu toc do).

Architecture:
- Tat ca data (agents list, cookies) cached trong QSettings (0ms read)
- DB chi dung de sync (background, khong block UI)
- Fetch upstream truc tiep bang cookies local

Flow toi uu:
1. Login app → on_login_success → sync_from_db (background)
   → cache agents + cookies vao QSettings
2. Show customer tab → doc QSettings (0ms) → fetch upstream truc tiep
3. Login EE88 (account tab) → server luu cookie DB
   → sync_from_db (background) → update QSettings
4. Logout app → clear QSettings cache

Usage:
    from utils.upstream import upstream

    # Sync 1 lan sau login (background)
    upstream.sync_from_db("admin")

    # Doc agents (instant, tu QSettings)
    agents = upstream.get_agents_local()

    # Fetch upstream (doc cookie tu QSettings → goi upstream truc tiep)
    data = upstream.fetch_customers(agent_id=1, page=1, limit=50)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "https://a2u4k.ee88dly.com")


def _get_db():
    from utils.db import Database
    return Database()


def _settings():
    from utils.settings import settings
    return settings


class UpstreamClient:
    """Local-first upstream client. Moi data doc tu QSettings, 0 network."""

    # ══════════════════════════════════════════════════════════
    #  LOCAL STORAGE — QSettings (instant read/write)
    # ══════════════════════════════════════════════════════════

    def save_agents_local(self, agents: list[dict]) -> None:
        """Cache agents + cookies vao QSettings."""
        s = _settings()
        cache = []
        for ag in agents:
            cache.append({
                "id": ag["id"],
                "name": ag["name"],
                "ext_username": ag["ext_username"],
                "base_url": ag.get("base_url") or "",
                "status": ag.get("status", ""),
            })
            cookie = ag.get("session_cookie")
            if cookie:
                s.set(f"agent/{ag['id']}/cookie", cookie)
                s.set(f"agent/{ag['id']}/base_url", ag.get("base_url") or UPSTREAM_BASE_URL)
        s.set("agents/cache", json.dumps(cache))

    def get_agents_local(self) -> list[dict]:
        """Doc agents tu QSettings cache (0ms). [] neu chua sync."""
        raw = _settings().get_str("agents/cache")
        if not raw:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []

    def get_cookie(self, agent_id: int) -> tuple[str, str] | None:
        """Doc cookie tu QSettings (0ms). None neu khong co."""
        s = _settings()
        cookie = s.get_str(f"agent/{agent_id}/cookie")
        if not cookie:
            return None
        base_url = s.get_str(f"agent/{agent_id}/base_url", UPSTREAM_BASE_URL)
        return cookie, base_url.rstrip("/")

    def save_cookie(self, agent_id: int, cookie: str, base_url: str = "") -> None:
        """Luu cookie vao QSettings."""
        s = _settings()
        s.set(f"agent/{agent_id}/cookie", cookie)
        s.set(f"agent/{agent_id}/base_url", base_url or UPSTREAM_BASE_URL)

    def clear_local(self) -> None:
        """Xoa toan bo cache local (khi logout)."""
        s = _settings()
        s.remove("agents/cache")
        # Xoa cookies cua tat ca agents da cache
        for ag in self.get_agents_local():
            s.remove(f"agent/{ag['id']}/cookie")
            s.remove(f"agent/{ag['id']}/base_url")

    # ══════════════════════════════════════════════════════════
    #  DB SYNC — chay trong worker thread, KHONG block UI
    # ══════════════════════════════════════════════════════════

    def sync_from_db(self, username: str) -> list[dict]:
        """Dong bo agents + cookies tu VPS DB xuong QSettings.
        Goi trong worker thread. Tra ve agents list."""
        with _get_db() as db:
            agents = db.fetchall(
                "SELECT a.id, a.name, a.ext_username, a.session_cookie, "
                "a.base_url, a.status "
                "FROM agents a JOIN users u ON a.user_id = u.id "
                "WHERE u.username = %s AND a.is_active = TRUE "
                "ORDER BY a.id",
                (username,),
            )
        self.save_agents_local(agents)
        logger.info("Synced %d agents from DB for %s", len(agents), username)
        return agents

    # ══════════════════════════════════════════════════════════
    #  UPSTREAM FETCH — goi truc tiep bang cookies local
    # ══════════════════════════════════════════════════════════

    def _post(self, cookie: str, base_url: str, path: str, data: str) -> dict[str, Any]:
        """POST upstream voi PHPSESSID cookie."""
        url = f"{base_url}{path}"
        resp = requests.post(
            url,
            data=data,
            headers={**_DEFAULT_HEADERS, "Cookie": f"PHPSESSID={cookie}"},
            timeout=15,
            verify=False,
            allow_redirects=False,
        )

        if resp.status_code in (301, 302):
            loc = resp.headers.get("Location", "").lower()
            if "login" in loc:
                raise PermissionError("Session expired.")
            raise ConnectionError(f"Upstream redirect: {resp.status_code}")

        if resp.status_code != 200:
            raise ConnectionError(f"Upstream HTTP {resp.status_code}")

        try:
            result = resp.json()
        except ValueError:
            if "login" in resp.text[:200].lower():
                raise PermissionError("Session expired.")
            raise ConnectionError("Upstream returned non-JSON.")

        if result.get("url", "").startswith("/agent/login"):
            raise PermissionError("Session expired.")

        return result

    def fetch_customers(
        self, agent_id: int,
        page: int = 1, limit: int = 50, username: str = "",
    ) -> dict[str, Any]:
        """Fetch customers tu upstream. Doc cookie tu QSettings (0ms)."""
        cached = self.get_cookie(agent_id)
        if not cached:
            raise ValueError("No session. Login agent first.")

        cookie, base_url = cached
        params = f"page={page}&limit={limit}"
        if username:
            params += f"&username={username}"

        result = self._post(cookie, base_url, "/agent/user.html", params)

        if result.get("code") != 0:
            raise ConnectionError(f"Upstream: {result.get('msg', 'error')}")

        return {
            "ok": True,
            "data": result.get("data", []),
            "count": result.get("count", 0),
            "page": page,
            "limit": limit,
        }


# Singleton
upstream = UpstreamClient()
