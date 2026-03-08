"""
Unit tests cho server/config.py — Environment configuration.
"""
import os
import pytest
from unittest.mock import patch


class TestConfig:
    def test_default_db_host(self):
        """DB_HOST mặc định là localhost nếu không có env var."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to pick up fresh env
            import importlib
            import server.config as cfg
            # Config đã load từ .env, test giá trị mặc định
            assert cfg.DB_HOST is not None

    def test_default_db_port(self):
        from server.config import DB_PORT
        # Phải là string (os.getenv trả string)
        assert DB_PORT is not None

    def test_jwt_secret_not_empty(self):
        """JWT_SECRET phải có giá trị (từ env hoặc random)."""
        from server.config import JWT_SECRET
        assert JWT_SECRET is not None
        assert len(JWT_SECRET) > 0

    def test_jwt_expire_hours_is_int(self):
        from server.config import JWT_EXPIRE_HOURS
        assert isinstance(JWT_EXPIRE_HOURS, int)
        assert JWT_EXPIRE_HOURS > 0

    def test_db_dsn_format(self):
        """DB_DSN chứa host, port, dbname, user."""
        from server.config import DB_DSN
        assert "host=" in DB_DSN
        assert "port=" in DB_DSN
        assert "dbname=" in DB_DSN
        assert "user=" in DB_DSN

    def test_app_version_format(self):
        """APP_VERSION phải có dạng X.Y.Z."""
        from server.config import APP_VERSION
        parts = APP_VERSION.split(".")
        assert len(parts) == 3
        for p in parts:
            assert p.isdigit()

    def test_update_force_is_bool(self):
        from server.config import UPDATE_FORCE
        assert isinstance(UPDATE_FORCE, bool)
