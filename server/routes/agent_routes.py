"""
server/routes/agent_routes.py — Agent (dai ly) CRUD + upstream login.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from server.config import UPSTREAM_BASE_URL
from server.database import get_db
from server.auth import get_current_user
from server.models import (
    AgentCreateReq, AgentUpdateReq, AgentResp, AgentLoginReq, MsgResp,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

DEFAULT_UPSTREAM_URL = UPSTREAM_BASE_URL


def _agent_row_to_dict(row: dict) -> dict:
    """Convert DB row to safe dict (exclude ext_password, session_cookie)."""
    return {
        "id": row["id"],
        "name": row["name"],
        "ext_username": row["ext_username"],
        "has_password": bool(row.get("ext_password")),
        "base_url": row.get("base_url") or DEFAULT_UPSTREAM_URL,
        "status": row.get("status", "offline"),
        "is_active": row.get("is_active", True),
        "login_error": row.get("login_error"),
        "last_login_at": row["last_login_at"].isoformat() if row.get("last_login_at") else None,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


@router.get("", response_model=AgentResp)
def list_agents(user: dict = Depends(get_current_user), db=Depends(get_db)):
    """List all agents for current user."""
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM agents WHERE user_id = %s AND is_active = TRUE ORDER BY created_at",
        (user["id"],),
    )
    rows = cur.fetchall()
    return AgentResp(ok=True, agents=[_agent_row_to_dict(r) for r in rows])


@router.post("", response_model=AgentResp)
def create_agent(
    req: AgentCreateReq,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Create a new agent."""
    cur = db.cursor()
    # Check duplicate
    cur.execute(
        "SELECT id FROM agents WHERE user_id = %s AND ext_username = %s",
        (user["id"], req.ext_username),
    )
    if cur.fetchone():
        return AgentResp(ok=False, message="server.agent_username_exists")

    cur.execute(
        """INSERT INTO agents (user_id, name, ext_username, ext_password, base_url)
           VALUES (%s, %s, %s, %s, %s) RETURNING *""",
        (user["id"], req.name, req.ext_username, req.ext_password, req.base_url),
    )
    row = cur.fetchone()
    logger.info("Agent created: %s (%s) by user %s", req.name, req.ext_username, user["id"])
    return AgentResp(ok=True, agent=_agent_row_to_dict(row))


@router.put("/{agent_id}", response_model=AgentResp)
def update_agent(
    agent_id: int,
    req: AgentUpdateReq,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update agent details."""
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM agents WHERE id = %s AND user_id = %s",
        (agent_id, user["id"]),
    )
    agent = cur.fetchone()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    updates = []
    params = []
    if req.name is not None:
        updates.append("name = %s")
        params.append(req.name)
    if req.ext_password is not None:
        updates.append("ext_password = %s")
        params.append(req.ext_password)
    if req.base_url is not None:
        updates.append("base_url = %s")
        params.append(req.base_url)

    if not updates:
        return AgentResp(ok=True, agent=_agent_row_to_dict(agent))

    updates.append("updated_at = NOW()")
    params.extend([agent_id, user["id"]])
    cur.execute(
        f"UPDATE agents SET {', '.join(updates)} WHERE id = %s AND user_id = %s RETURNING *",
        params,
    )
    row = cur.fetchone()
    return AgentResp(ok=True, agent=_agent_row_to_dict(row))


@router.delete("/{agent_id}", response_model=MsgResp)
def delete_agent(
    agent_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Soft-delete agent."""
    cur = db.cursor()
    cur.execute(
        "UPDATE agents SET is_active = FALSE, updated_at = NOW() "
        "WHERE id = %s AND user_id = %s",
        (agent_id, user["id"]),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return MsgResp(ok=True, message="server.agent_deleted")


@router.post("/{agent_id}/login", response_model=AgentResp)
def login_agent(
    agent_id: int,
    req: AgentLoginReq | None = None,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Login agent to upstream EE88 platform."""
    from utils.upstream_auth import login_upstream

    cur = db.cursor()
    cur.execute(
        "SELECT * FROM agents WHERE id = %s AND user_id = %s AND is_active = TRUE",
        (agent_id, user["id"]),
    )
    agent = cur.fetchone()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    if not agent["ext_password"]:
        return AgentResp(ok=False, message="server.agent_no_password")

    base_url = (req and req.base_url) or agent.get("base_url") or DEFAULT_UPSTREAM_URL

    # Set status to logging_in
    cur.execute(
        "UPDATE agents SET status = 'logging_in', login_error = NULL WHERE id = %s",
        (agent_id,),
    )

    result = login_upstream(
        username=agent["ext_username"],
        password=agent["ext_password"],
        base_url=base_url,
    )

    now = datetime.now(timezone.utc)

    if result["success"]:
        cookie_expires = datetime.fromtimestamp(
            now.timestamp() + 24 * 3600, tz=timezone.utc,
        )
        cur.execute(
            """UPDATE agents SET
                session_cookie = %s, cookie_expires = %s,
                status = 'active', last_login_at = %s,
                login_error = NULL, login_attempts = 0,
                updated_at = NOW()
               WHERE id = %s RETURNING *""",
            (result["session_id"], cookie_expires, now, agent_id),
        )
        row = cur.fetchone()
        logger.info("Agent %s logged in, captcha_attempts=%d", agent["name"], result["captcha_attempts"])
        return AgentResp(ok=True, agent=_agent_row_to_dict(row))

    # Failed
    cur.execute(
        """UPDATE agents SET
            status = 'error', login_error = %s,
            login_attempts = login_attempts + 1,
            updated_at = NOW()
           WHERE id = %s RETURNING *""",
        (result["error"], agent_id),
    )
    row = cur.fetchone()
    return AgentResp(ok=False, agent=_agent_row_to_dict(row), message=result["error"])


@router.post("/{agent_id}/logout", response_model=MsgResp)
def logout_agent(
    agent_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Logout agent from upstream."""
    from utils.upstream_auth import logout_upstream

    cur = db.cursor()
    cur.execute(
        "SELECT * FROM agents WHERE id = %s AND user_id = %s",
        (agent_id, user["id"]),
    )
    agent = cur.fetchone()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    if agent["session_cookie"]:
        base_url = agent.get("base_url") or DEFAULT_UPSTREAM_URL
        logout_upstream(agent["session_cookie"], base_url)

    cur.execute(
        """UPDATE agents SET
            session_cookie = '', cookie_expires = NULL,
            status = 'offline', login_error = NULL,
            updated_at = NOW()
           WHERE id = %s""",
        (agent_id,),
    )
    return MsgResp(ok=True, message="server.agent_logged_out")


@router.post("/{agent_id}/check", response_model=AgentResp)
def check_agent(
    agent_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Check if agent session is still valid."""
    from utils.upstream_auth import check_session

    cur = db.cursor()
    cur.execute(
        "SELECT * FROM agents WHERE id = %s AND user_id = %s",
        (agent_id, user["id"]),
    )
    agent = cur.fetchone()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")

    if not agent["session_cookie"]:
        return AgentResp(ok=False, message="server.agent_no_session", agent=_agent_row_to_dict(agent))

    base_url = agent.get("base_url") or DEFAULT_UPSTREAM_URL
    valid = check_session(agent["session_cookie"], base_url)

    if valid:
        if agent["status"] != "active":
            cur.execute(
                "UPDATE agents SET status = 'active', login_error = NULL WHERE id = %s",
                (agent_id,),
            )
        agent["status"] = "active"
        return AgentResp(ok=True, agent=_agent_row_to_dict(agent))

    cur.execute(
        "UPDATE agents SET status = 'error', login_error = 'server.agent_session_expired' WHERE id = %s",
        (agent_id,),
    )
    agent["status"] = "error"
    agent["login_error"] = "server.agent_session_expired"
    return AgentResp(ok=False, message="server.agent_session_expired", agent=_agent_row_to_dict(agent))
