"""
server/routes/group_routes.py — Group management + data sync (Phuong an E).

Endpoints:
  POST   /api/groups                     — Tao nhom moi
  GET    /api/groups                     — List nhom cua user
  GET    /api/groups/{id}                — Chi tiet nhom
  PUT    /api/groups/{id}                — Cap nhat nhom
  DELETE /api/groups/{id}                — Xoa nhom (soft delete)

  POST   /api/groups/{id}/agents         — Them agent vao nhom (bang agent_key)
  DELETE /api/groups/{id}/agents/{aid}   — Xoa agent khoi nhom
  GET    /api/groups/{id}/agents         — List agents + cookies (cho member)

  POST   /api/groups/{id}/sync           — Client push data len cache
  GET    /api/groups/{id}/cache          — Doc cache
  GET    /api/groups/{id}/cache/version  — Lightweight poll version
"""
import asyncio
import logging
import secrets
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from server.database import get_db
from server.auth import get_current_user
from server.config import UPSTREAM_BASE_URL
from server.ws_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["groups"])


# ── Helpers ───────────────────────────────────────────────────

def _verify_group_access(cur, group_id: int, user_id: int) -> dict:
    """Verify user has access to group (owner or has agent in group).
    Returns group dict or raises 403/404."""
    cur.execute(
        "SELECT * FROM groups WHERE id = %s AND deleted_at IS NULL",
        (group_id,),
    )
    group = cur.fetchone()
    if not group:
        raise HTTPException(404, "Group not found.")

    # Owner always has access
    if group["owner_id"] == user_id:
        return group

    # Member = has at least 1 agent in this group
    cur.execute(
        "SELECT 1 FROM agents WHERE group_id = %s AND user_id = %s AND is_active = TRUE LIMIT 1",
        (group_id, user_id),
    )
    if not cur.fetchone():
        raise HTTPException(403, "No access to this group.")

    return group


def _verify_group_owner(cur, group_id: int, user_id: int) -> dict:
    """Verify user is owner of group. Returns group dict or raises."""
    cur.execute(
        "SELECT * FROM groups WHERE id = %s AND owner_id = %s AND deleted_at IS NULL",
        (group_id, user_id),
    )
    group = cur.fetchone()
    if not group:
        raise HTTPException(404, "Group not found or not owner.")
    return group


def _audit_log(cur, group_id: int, user_id: int, action: str,
               target_agent_id: int | None = None, details: dict | None = None):
    cur.execute(
        "INSERT INTO group_audit_log (group_id, user_id, action, target_agent_id, details) "
        "VALUES (%s, %s, %s, %s, %s)",
        (group_id, user_id, action, target_agent_id, json.dumps(details or {})),
    )


def _generate_agent_key() -> str:
    """Generate 12-char alphanumeric key."""
    return secrets.token_hex(6).upper()


def _broadcast_sync(group_id: int, event: dict) -> None:
    """Helper: broadcast tu sync context (non-async endpoint chay trong threadpool)."""
    loop = ws_manager._loop
    if not loop or loop.is_closed():
        logger.warning("broadcast_sync: no event loop available")
        return
    future = asyncio.run_coroutine_threadsafe(
        ws_manager.broadcast(group_id, event), loop,
    )
    try:
        # Wait up to 2s for broadcast to complete
        sent = future.result(timeout=2)
        logger.info("broadcast_sync: group=%d sent=%d", group_id, sent)
    except Exception as e:
        logger.error("broadcast_sync failed: %s", e)


# ── Group CRUD ────────────────────────────────────────────────

@router.post("")
def create_group(
    body: dict,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Group name required.")

    cur = db.cursor()
    cur.execute(
        "INSERT INTO groups (name, description, owner_id) VALUES (%s, %s, %s) RETURNING *",
        (name, body.get("description", ""), user["id"]),
    )
    group = cur.fetchone()
    _audit_log(cur, group["id"], user["id"], "group_created")
    return {"ok": True, "group": _group_to_dict(group, user["id"])}


@router.get("")
def list_groups(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    # Groups user owns OR has agent in
    cur.execute(
        """SELECT DISTINCT g.* FROM groups g
           LEFT JOIN agents a ON a.group_id = g.id AND a.user_id = %s AND a.is_active = TRUE
           WHERE g.deleted_at IS NULL
             AND (g.owner_id = %s OR a.id IS NOT NULL)
           ORDER BY g.created_at DESC""",
        (user["id"], user["id"]),
    )
    groups = cur.fetchall()
    return {
        "ok": True,
        "groups": [_group_to_dict(g, user["id"]) for g in groups],
    }


@router.get("/{group_id}")
def get_group(
    group_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    group = _verify_group_access(cur, group_id, user["id"])

    # Count agents in group
    cur.execute(
        "SELECT COUNT(*) as cnt FROM agents WHERE group_id = %s AND is_active = TRUE",
        (group_id,),
    )
    count = cur.fetchone()["cnt"]

    result = _group_to_dict(group, user["id"])
    result["member_count"] = count
    return {"ok": True, "group": result}


@router.put("/{group_id}")
def update_group(
    group_id: int,
    body: dict,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    _verify_group_owner(cur, group_id, user["id"])

    updates, params = [], []
    for field in ("name", "description", "max_members"):
        if field in body:
            updates.append(f"{field} = %s")
            params.append(body[field])

    if not updates:
        raise HTTPException(400, "Nothing to update.")

    updates.append("updated_at = NOW()")
    params.extend([group_id, user["id"]])
    cur.execute(
        f"UPDATE groups SET {', '.join(updates)} WHERE id = %s AND owner_id = %s RETURNING *",
        params,
    )
    group = cur.fetchone()
    return {"ok": True, "group": _group_to_dict(group, user["id"])}


@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    _verify_group_owner(cur, group_id, user["id"])

    # Remove all agents from group
    cur.execute(
        "UPDATE agents SET group_id = NULL, group_joined_at = NULL WHERE group_id = %s",
        (group_id,),
    )
    # Soft delete group
    cur.execute(
        "UPDATE groups SET deleted_at = NOW() WHERE id = %s",
        (group_id,),
    )
    _audit_log(cur, group_id, user["id"], "group_deleted")
    return {"ok": True, "message": "Group deleted."}


def _group_to_dict(g: dict, user_id: int) -> dict:
    return {
        "id": g["id"],
        "name": g["name"],
        "description": g.get("description", ""),
        "owner_id": g["owner_id"],
        "is_owner": g["owner_id"] == user_id,
        "max_members": g.get("max_members", 50),
        "is_active": g.get("is_active", True),
        "created_at": g["created_at"].isoformat() if g.get("created_at") else None,
    }


# ── Agent management in group ─────────────────────────────────

@router.post("/{group_id}/agents")
def add_agent_to_group(
    group_id: int,
    body: dict,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Add agent to group by agent_key."""
    agent_key = body.get("agent_key", "").strip().upper()
    if not agent_key:
        raise HTTPException(400, "agent_key required.")

    cur = db.cursor()
    _verify_group_owner(cur, group_id, user["id"])

    # Find agent by key
    cur.execute(
        "SELECT * FROM agents WHERE agent_key = %s AND is_active = TRUE",
        (agent_key,),
    )
    agent = cur.fetchone()
    if not agent:
        raise HTTPException(404, "Agent not found with this key.")

    if agent["group_id"] and agent["group_id"] != group_id:
        raise HTTPException(400, "Agent already belongs to another group.")

    # Check max members
    cur.execute(
        "SELECT COUNT(*) as cnt FROM agents WHERE group_id = %s AND is_active = TRUE",
        (group_id,),
    )
    count = cur.fetchone()["cnt"]
    cur.execute("SELECT max_members FROM groups WHERE id = %s", (group_id,))
    max_m = cur.fetchone()["max_members"]
    if count >= max_m:
        raise HTTPException(400, "Group is full.")

    # Add to group
    now = datetime.now(timezone.utc)
    cur.execute(
        "UPDATE agents SET group_id = %s, group_joined_at = %s WHERE id = %s RETURNING *",
        (group_id, now, agent["id"]),
    )
    _audit_log(cur, group_id, user["id"], "agent_added", agent["id"],
               {"agent_name": agent["name"]})
    _broadcast_sync(group_id, {
        "type": "member_added",
        "group_id": group_id,
        "agent_name": agent["name"],
        "added_by": user["username"],
    })
    return {"ok": True, "message": "Agent added to group."}


@router.delete("/{group_id}/agents/{agent_id}")
def remove_agent_from_group(
    group_id: int,
    agent_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    _verify_group_owner(cur, group_id, user["id"])

    cur.execute(
        "UPDATE agents SET group_id = NULL, group_joined_at = NULL "
        "WHERE id = %s AND group_id = %s",
        (agent_id, group_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(404, "Agent not in this group.")

    _audit_log(cur, group_id, user["id"], "agent_removed", agent_id)
    _broadcast_sync(group_id, {
        "type": "member_removed",
        "group_id": group_id,
        "agent_id": agent_id,
    })
    return {"ok": True, "message": "Agent removed from group."}


@router.get("/{group_id}/agents")
def get_group_agents(
    group_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all agents + cookies in group. Only for group members."""
    cur = db.cursor()
    _verify_group_access(cur, group_id, user["id"])

    cur.execute(
        """SELECT id, name, ext_username, session_cookie, base_url,
                  status, user_id
           FROM agents
           WHERE group_id = %s AND is_active = TRUE
           ORDER BY name""",
        (group_id,),
    )
    agents = cur.fetchall()

    return {
        "ok": True,
        "agents": [
            {
                "id": a["id"],
                "name": a["name"],
                "ext_username": a["ext_username"],
                "session_cookie": a["session_cookie"],
                "base_url": a.get("base_url") or UPSTREAM_BASE_URL,
                "status": a["status"],
                "is_mine": a["user_id"] == user["id"],
            }
            for a in agents
        ],
    }


# ── Agent key generation ──────────────────────────────────────

@router.post("/agent-key/{agent_id}")
def generate_agent_key(
    agent_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Generate a shareable key for an agent (owner only)."""
    cur = db.cursor()
    cur.execute(
        "SELECT * FROM agents WHERE id = %s AND user_id = %s AND is_active = TRUE",
        (agent_id, user["id"]),
    )
    agent = cur.fetchone()
    if not agent:
        raise HTTPException(404, "Agent not found.")

    key = _generate_agent_key()
    cur.execute(
        "UPDATE agents SET agent_key = %s, key_generated_at = NOW() WHERE id = %s",
        (key, agent_id),
    )
    return {"ok": True, "agent_key": key}


# ── Data sync (Phuong an E) ──────────────────────────────────

@router.post("/{group_id}/sync")
def sync_group_data(
    group_id: int,
    body: dict,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Client push fetched data to server cache."""
    cur = db.cursor()
    _verify_group_access(cur, group_id, user["id"])

    data_type = body.get("data_type", "")
    if not data_type:
        raise HTTPException(400, "data_type required.")

    data_json = body.get("data", [])
    agents_fetched = body.get("agents_fetched", [])
    agents_errors = body.get("agents_errors", [])
    total_count = len(data_json)

    cur.execute(
        """INSERT INTO group_data_cache
           (group_id, data_type, data_json, total_count,
            agents_fetched, agents_errors, synced_by, synced_at, version)
           VALUES (%s, %s, %s::jsonb, %s, %s::jsonb, %s::jsonb, %s, NOW(), 1)
           ON CONFLICT (group_id, data_type)
           DO UPDATE SET
             data_json = EXCLUDED.data_json,
             total_count = EXCLUDED.total_count,
             agents_fetched = EXCLUDED.agents_fetched,
             agents_errors = EXCLUDED.agents_errors,
             synced_by = EXCLUDED.synced_by,
             synced_at = NOW(),
             version = group_data_cache.version + 1
           RETURNING version""",
        (group_id, data_type,
         json.dumps(data_json), total_count,
         json.dumps(agents_fetched), json.dumps(agents_errors),
         user["id"]),
    )
    row = cur.fetchone()
    version = row["version"] if row else 1

    logger.info("Group %d sync %s: %d rows, version=%d by user %d",
                group_id, data_type, total_count, version, user["id"])

    _broadcast_sync(group_id, {
        "type": "data_updated",
        "group_id": group_id,
        "data_type": data_type,
        "version": version,
        "synced_by": user["username"],
        "synced_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"ok": True, "version": version}


@router.get("/{group_id}/cache")
def get_group_cache(
    group_id: int,
    data_type: str = Query(...),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Read cached data for group."""
    cur = db.cursor()
    _verify_group_access(cur, group_id, user["id"])

    cur.execute(
        """SELECT data_json, total_count, version, synced_at,
                  agents_fetched, agents_errors
           FROM group_data_cache
           WHERE group_id = %s AND data_type = %s""",
        (group_id, data_type),
    )
    row = cur.fetchone()
    if not row:
        return {"ok": False, "message": "No cache."}

    return {
        "ok": True,
        "data": row["data_json"],
        "total_count": row["total_count"],
        "version": row["version"],
        "synced_at": row["synced_at"].isoformat() if row["synced_at"] else None,
        "agents_fetched": row["agents_fetched"],
        "agents_errors": row["agents_errors"],
    }


@router.get("/{group_id}/cache/version")
def get_group_cache_version(
    group_id: int,
    data_type: str = Query(...),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Lightweight poll — only return version + synced_at."""
    cur = db.cursor()
    _verify_group_access(cur, group_id, user["id"])

    cur.execute(
        "SELECT version, synced_at FROM group_data_cache "
        "WHERE group_id = %s AND data_type = %s",
        (group_id, data_type),
    )
    row = cur.fetchone()
    if not row:
        return {"version": 0, "synced_at": None}

    return {
        "version": row["version"],
        "synced_at": row["synced_at"].isoformat() if row["synced_at"] else None,
    }
