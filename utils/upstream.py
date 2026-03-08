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
        # AUDIT-FIX: read cache BEFORE removing, otherwise get_agents_local() returns []
        agents = self.get_agents_local()
        s.remove("agents/cache")
        # Xoa cookies cua tat ca agents da cache
        for ag in agents:
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

    def _auto_relogin(self, agent_id: int) -> tuple[str, str] | None:
        """Auto re-login agent khi upstream session het han.

        Goi API server /api/agents/{id}/login → nhan cookie moi → luu QSettings.
        Returns (cookie, base_url) hoac None.
        """
        from utils.api import api
        logger.info("Auto re-login agent %d...", agent_id)
        ok, data = api.post(f"/api/agents/{agent_id}/login")
        if not ok:
            logger.warning("Auto re-login failed for agent %d: %s", agent_id, data)
            return None

        agent_data = data.get("agent", {})
        new_cookie = agent_data.get("session_cookie", "")
        new_base = agent_data.get("base_url", UPSTREAM_BASE_URL)
        if not new_cookie:
            logger.warning("Auto re-login returned no cookie for agent %d", agent_id)
            return None

        self.save_cookie(agent_id, new_cookie, new_base)
        # Update agent status trong local cache
        agents = self.get_agents_local()
        for ag in agents:
            if ag["id"] == agent_id:
                ag["status"] = "active"
        self.save_agents_local(agents)

        logger.info("Auto re-login success for agent %d", agent_id)
        return new_cookie, new_base.rstrip("/")

    def _fetch(
        self, agent_id: int, path: str,
        page: int = 1, limit: int = 50, **kwargs: str,
    ) -> dict[str, Any]:
        """Generic fetch upstream. Doc cookie tu QSettings (0ms).
        Tu dong re-login neu session het han."""
        cached = self.get_cookie(agent_id)
        if not cached:
            raise ValueError("No session. Login agent first.")

        cookie, base_url = cached
        params = f"page={page}&limit={limit}"
        for k, v in kwargs.items():
            if v:
                params += f"&{k}={v}"

        try:
            result = self._post(cookie, base_url, path, params)
        except PermissionError:
            # Session expired → auto re-login
            new_session = self._auto_relogin(agent_id)
            if not new_session:
                raise PermissionError("Session expired. Auto re-login failed.")
            cookie, base_url = new_session
            result = self._post(cookie, base_url, path, params)

        if result.get("code") != 0:
            raise ConnectionError(f"Upstream: {result.get('msg', 'error')}")

        return {
            "ok": True,
            "data": result.get("data", []),
            "count": result.get("count", 0),
            "page": page,
            "limit": limit,
        }

    # ── Per-endpoint convenience methods ─────────────────────

    def fetch_customers(self, agent_id: int, page: int = 1, limit: int = 50,
                        **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/user.html",
                           page=page, limit=limit, hs_search="true", **kwargs)

    def fetch_deposits(self, agent_id: int, page: int = 1, limit: int = 50,
                       **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/depositAndWithdrawal.html",
                           page=page, limit=limit, **kwargs)

    def fetch_withdrawals(self, agent_id: int, page: int = 1, limit: int = 50,
                          **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/withdrawalsRecord.html",
                           page=page, limit=limit, **kwargs)

    def fetch_transactions(self, agent_id: int, page: int = 1, limit: int = 50,
                           **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/reportFunds.html",
                           page=page, limit=limit, **kwargs)

    def fetch_bet_lottery(self, agent_id: int, page: int = 1, limit: int = 50,
                          **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/bet.html",
                           page=page, limit=limit, es="1", is_summary="0",
                           **kwargs)

    def fetch_bet_provider(self, agent_id: int, page: int = 1, limit: int = 50,
                           **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/betOrder.html",
                           page=page, limit=limit, es="1", **kwargs)

    def fetch_lottery(self, agent_id: int, page: int = 1, limit: int = 50,
                      **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/reportLottery.html",
                           page=page, limit=limit, **kwargs)

    def fetch_provider(self, agent_id: int, page: int = 1, limit: int = 50,
                       **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/reportThirdGame.html",
                           page=page, limit=limit, **kwargs)

    def fetch_referrals(self, agent_id: int, page: int = 1, limit: int = 50,
                        **kwargs: str) -> dict[str, Any]:
        return self._fetch(agent_id, "/agent/inviteList.html",
                           page=page, limit=limit, **kwargs)

    # ══════════════════════════════════════════════════════════
    #  GROUP — Parallel fetch from multiple agents
    # ══════════════════════════════════════════════════════════

    def save_group_agents_local(self, group_id: int, agents: list[dict]) -> None:
        """Cache group agents + cookies vao QSettings."""
        s = _settings()
        for ag in agents:
            cookie = ag.get("session_cookie")
            if cookie:
                s.set(f"agent/{ag['id']}/cookie", cookie)
                s.set(f"agent/{ag['id']}/base_url",
                      ag.get("base_url") or UPSTREAM_BASE_URL)
        s.set(f"group/{group_id}/agents", json.dumps(agents))

    def get_group_agents_local(self, group_id: int) -> list[dict]:
        """Doc group agents tu QSettings cache (0ms)."""
        raw = _settings().get_str(f"group/{group_id}/agents")
        if not raw:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []

    def parallel_fetch(
        self,
        agents: list[dict],
        path: str,
        page: int = 1,
        limit: int = 50,
        extra_params: str = "",
    ) -> dict[str, Any]:
        """Fetch song song tu nhieu agents. Chay trong worker thread.

        Returns: {data: [...], agents_fetched: [...], agents_errors: [...]}
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        all_data: list[dict] = []
        agents_fetched: list[dict] = []
        agents_errors: list[dict] = []

        params = f"page={page}&limit={limit}"
        if extra_params:
            params += f"&{extra_params}"

        def _fetch_one(ag: dict) -> tuple[dict, list[dict]]:
            cookie_info = self.get_cookie(ag["id"])
            if not cookie_info:
                raise ValueError("no_session")
            cookie, base_url = cookie_info
            result = self._post(cookie, base_url, path, params)
            if result.get("code") != 0:
                raise ConnectionError(result.get("msg", "error"))
            rows = result.get("data", [])
            # Tag moi row voi agent info
            for row in rows:
                row["_agentId"] = ag["id"]
                row["_agentName"] = ag.get("name", "")
            return ag, rows

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(_fetch_one, ag): ag for ag in agents}

            for future in as_completed(futures):
                ag = futures[future]
                try:
                    _, rows = future.result()
                    all_data.extend(rows)
                    agents_fetched.append({
                        "id": ag["id"],
                        "name": ag.get("name", ""),
                        "row_count": len(rows),
                    })
                except Exception as e:
                    agents_errors.append({
                        "id": ag["id"],
                        "name": ag.get("name", ""),
                        "error": str(e),
                    })

        return {
            "data": all_data,
            "count": len(all_data),
            "agents_fetched": agents_fetched,
            "agents_errors": agents_errors,
        }


# Singleton
upstream = UpstreamClient()
