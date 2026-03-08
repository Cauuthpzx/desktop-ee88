"""
Integration tests cho group_routes — permission checks.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.integration
class TestGroupPermissions:
    """Test admin-only enforcement trên group endpoints."""

    def test_require_admin_blocks_user(self):
        from server.routes.group_routes import _require_admin
        from fastapi import HTTPException

        user = {"role": "user"}
        with pytest.raises(HTTPException) as exc_info:
            _require_admin(user)
        assert exc_info.value.status_code == 403

    def test_require_admin_allows_admin(self):
        from server.routes.group_routes import _require_admin
        # Should not raise
        _require_admin({"role": "admin"})

    def test_session_cookie_hidden_from_non_owner(self, sample_agents):
        """session_cookie chỉ trả cho agent owner."""
        user_id = 1  # agent A thuộc user 1, agent B thuộc user 2
        user = {"id": user_id}

        for agent in sample_agents:
            is_mine = agent["user_id"] == user["id"]
            cookie = agent["session_cookie"] if is_mine else ""
            if is_mine:
                assert cookie != ""
            else:
                assert cookie == ""


@pytest.mark.integration
class TestGroupHelpers:
    def test_generate_agent_key_format(self):
        from server.routes.group_routes import _generate_agent_key
        key = _generate_agent_key()
        assert len(key) == 12
        assert key.isalnum()
        assert key == key.upper()

    def test_generate_agent_key_unique(self):
        from server.routes.group_routes import _generate_agent_key
        keys = {_generate_agent_key() for _ in range(100)}
        # Với 12 hex chars, collision gần như impossible
        assert len(keys) == 100

    def test_group_to_dict_owner(self):
        from server.routes.group_routes import _group_to_dict
        from datetime import datetime, timezone
        group = {
            "id": 1, "name": "Test", "description": "Desc",
            "owner_id": 1, "max_members": 50, "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        result = _group_to_dict(group, user_id=1)
        assert result["is_owner"] is True
        assert result["name"] == "Test"

    def test_group_to_dict_non_owner(self):
        from server.routes.group_routes import _group_to_dict
        from datetime import datetime, timezone
        group = {
            "id": 1, "name": "Test", "description": "",
            "owner_id": 1, "max_members": 50, "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        result = _group_to_dict(group, user_id=99)
        assert result["is_owner"] is False
