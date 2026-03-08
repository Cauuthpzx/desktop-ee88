"""
Unit tests cho server/auth.py — JWT helpers.
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone


class TestCreateToken:
    def test_creates_valid_jwt(self):
        from server.auth import create_token, decode_token
        token = create_token(user_id=1, username="admin", role="admin", token_version=0)
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode should work
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"
        assert payload["tv"] == 0

    def test_token_contains_expiration(self):
        from server.auth import create_token, decode_token
        token = create_token(1, "user", "user", 0)
        payload = decode_token(token)
        assert "exp" in payload

    def test_different_users_get_different_tokens(self):
        from server.auth import create_token
        t1 = create_token(1, "alice", "user", 0)
        t2 = create_token(2, "bob", "user", 0)
        assert t1 != t2


class TestDecodeToken:
    def test_valid_token(self):
        from server.auth import create_token, decode_token
        token = create_token(1, "admin", "admin", 0)
        payload = decode_token(token)
        assert payload["username"] == "admin"

    def test_expired_token_raises(self):
        import jwt
        from server.config import JWT_SECRET
        from fastapi import HTTPException

        payload = {
            "sub": "1",
            "username": "admin",
            "role": "admin",
            "tv": 0,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        from server.auth import decode_token
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_invalid_token_raises(self):
        from server.auth import decode_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises(self):
        import jwt
        from fastapi import HTTPException

        payload = {
            "sub": "1",
            "username": "admin",
            "role": "admin",
            "tv": 0,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        from server.auth import decode_token
        with pytest.raises(HTTPException):
            decode_token(token)


class TestReservedUsernames:
    @pytest.mark.parametrize("name", ["admin", "administrator", "root", "system"])
    def test_reserved_names_blocked(self, name):
        from server.routes.auth_routes import RESERVED_USERNAMES
        assert name in RESERVED_USERNAMES

    def test_normal_name_allowed(self):
        from server.routes.auth_routes import RESERVED_USERNAMES
        assert "alice" not in RESERVED_USERNAMES
        assert "bob" not in RESERVED_USERNAMES
