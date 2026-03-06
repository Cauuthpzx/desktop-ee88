"""
server/routes/upstream_routes.py — Proxy upstream data qua session cookie.

Desktop app goi endpoint nay → server dung session_cookie cua agent
→ fetch data tu upstream EE88 → tra ve cho desktop.
"""
import logging
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Query

from server.config import UPSTREAM_BASE_URL
from server.database import get_db
from server.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upstream", tags=["upstream"])

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


def _get_agent_session(agent_id: int, user_id: int, db) -> tuple[str, str]:
    """Return (session_cookie, base_url) for an active agent.

    Raises HTTPException if agent not found or session invalid.
    """
    cur = db.cursor()
    cur.execute(
        "SELECT session_cookie, base_url, status FROM agents "
        "WHERE id = %s AND user_id = %s AND is_active = TRUE",
        (agent_id, user_id),
    )
    agent = cur.fetchone()
    if not agent:
        raise HTTPException(404, "Agent not found.")
    if not agent["session_cookie"]:
        raise HTTPException(400, "Agent has no active session. Please login first.")
    if agent["status"] != "active":
        raise HTTPException(400, f"Agent status is '{agent['status']}', not active.")

    base_url = agent.get("base_url") or UPSTREAM_BASE_URL
    return agent["session_cookie"], base_url.rstrip("/")


def _upstream_post(
    session_cookie: str,
    base_url: str,
    path: str,
    data: str,
) -> dict[str, Any]:
    """POST to upstream with PHPSESSID cookie. Returns parsed JSON."""
    url = f"{base_url}{path}"
    try:
        resp = requests.post(
            url,
            data=data,
            headers={**_DEFAULT_HEADERS, "Cookie": f"PHPSESSID={session_cookie}"},
            timeout=15,
            verify=False,
            allow_redirects=False,
        )
    except requests.RequestException as e:
        logger.error("Upstream request failed: %s", e)
        raise HTTPException(502, f"Upstream request failed: {e}")

    if resp.status_code in (301, 302):
        location = resp.headers.get("Location", "").lower()
        if "login" in location:
            raise HTTPException(401, "Upstream session expired. Please re-login agent.")
        raise HTTPException(502, f"Upstream redirect: {resp.status_code}")

    if resp.status_code != 200:
        raise HTTPException(502, f"Upstream HTTP {resp.status_code}")

    try:
        result = resp.json()
    except ValueError:
        text = resp.text[:200].lower()
        if "login" in text:
            raise HTTPException(401, "Upstream session expired.")
        raise HTTPException(502, "Upstream returned non-JSON response.")

    # Check for login redirect in response body
    if result.get("url", "").startswith("/agent/login"):
        raise HTTPException(401, "Upstream session expired. Please re-login agent.")

    return result


# ── Customers (users) ──────────────────────────────────────────

@router.get("/customers")
def get_customers(
    agent_id: int = Query(..., description="Agent ID to use for upstream fetch"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    username: str = Query("", description="Filter by username"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Fetch customer list from upstream via agent session."""
    session_cookie, base_url = _get_agent_session(agent_id, user["id"], db)

    # Build form data
    params = f"page={page}&limit={limit}"
    if username:
        params += f"&username={username}"

    result = _upstream_post(session_cookie, base_url, "/agent/user.html", params)

    code = result.get("code")
    if code != 0:
        msg = result.get("msg", "Unknown error")
        raise HTTPException(502, f"Upstream error: {msg}")

    return {
        "ok": True,
        "data": result.get("data", []),
        "count": result.get("count", 0),
        "page": page,
        "limit": limit,
    }
