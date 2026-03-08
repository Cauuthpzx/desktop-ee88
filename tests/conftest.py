"""
tests/conftest.py — Shared fixtures cho toàn bộ test suite.

Fixtures:
    - qapp: QApplication instance (auto-reuse, session scope)
    - mock_api: Mock ApiClient không gọi network
    - mock_settings: AppSettings tạm, không ảnh hưởng registry
    - sample_agents: Dữ liệu agent mẫu
    - i18n_init: Khởi tạo i18n cho tests cần t()
"""
from __future__ import annotations

import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch

# Đảm bảo project root nằm trong sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── QApplication fixture (session scope — tạo 1 lần) ────────
@pytest.fixture(scope="session")
def qapp():
    """Tạo QApplication cho UI tests. Reuse toàn session."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# ── i18n init ─────────────────────────────────────────────────
@pytest.fixture
def i18n_init():
    """Khởi tạo i18n module — cần cho tests dùng t()."""
    from core.i18n import init
    init()


# ── Mock API client ──────────────────────────────────────────
@pytest.fixture
def mock_api():
    """ApiClient giả, không gọi network."""
    from utils.api import ApiClient
    client = ApiClient.__new__(ApiClient)
    client._base = "http://test:8000"
    client._token = "test-jwt-token"
    client._username = "testuser"
    client._role = "admin"
    import threading
    client._lock = threading.Lock()
    return client


# ── Mock settings (in-memory, không ghi registry) ─────────────
@pytest.fixture
def mock_settings():
    """AppSettings giả dùng dict nội bộ thay QSettings."""
    store: dict = {}

    class FakeSettings:
        def set(self, key: str, value):
            store[key] = value

        def get(self, key: str, default=None):
            return store.get(key, default)

        def get_int(self, key: str, default: int = 0) -> int:
            try:
                return int(store.get(key, default))
            except (TypeError, ValueError):
                return default

        def get_bool(self, key: str, default: bool = False) -> bool:
            val = store.get(key, default)
            if isinstance(val, bool):
                return val
            return str(val).lower() in ("true", "1", "yes")

        def get_str(self, key: str, default: str = "") -> str:
            return str(store.get(key, default) or default)

        def remove(self, key: str):
            store.pop(key, None)

        def clear(self):
            store.clear()

        def all_keys(self) -> list[str]:
            return list(store.keys())

    return FakeSettings()


# ── Sample data ──────────────────────────────────────────────
@pytest.fixture
def sample_agents() -> list[dict]:
    return [
        {
            "id": 1,
            "name": "Agent A",
            "ext_username": "agent_a",
            "session_cookie": "cookie_a",
            "base_url": "https://example.com",
            "status": "online",
            "user_id": 1,
        },
        {
            "id": 2,
            "name": "Agent B",
            "ext_username": "agent_b",
            "session_cookie": "cookie_b",
            "base_url": "https://example.com",
            "status": "offline",
            "user_id": 2,
        },
    ]


@pytest.fixture
def sample_user() -> dict:
    return {
        "id": 1,
        "username": "admin",
        "role": "admin",
        "status": "active",
        "token_version": 0,
    }


# ── Fixtures file path ──────────────────────────────────────
@pytest.fixture
def fixtures_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures")
