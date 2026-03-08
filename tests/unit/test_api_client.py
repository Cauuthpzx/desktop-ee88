"""
Unit tests cho utils/api.py — ApiClient.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def _init_i18n():
    from core.i18n import init
    init()


class TestApiClientInit:
    def test_default_base_url(self):
        from utils.api import ApiClient
        with patch.dict("os.environ", {"API_URL": "http://test:9000"}, clear=False):
            client = ApiClient()
            assert client._base == "http://test:9000"

    def test_initial_state(self):
        from utils.api import ApiClient
        client = ApiClient()
        assert client.token is None
        assert client.username is None
        assert client.role is None
        assert client.is_logged_in is False


class TestApiClientLogin:
    def test_login_success_sets_token(self, mock_api):
        """Login thành công phải set token, username, role."""
        with patch.object(mock_api, "post", return_value=(
            True, {"ok": True, "token": "new-token", "username": "admin", "role": "admin"}
        )):
            ok, msg = mock_api.login("admin", "123456")
            assert ok is True
            assert mock_api.token == "new-token"
            assert mock_api.username == "admin"

    def test_login_failure_returns_message(self, mock_api):
        with patch.object(mock_api, "post", return_value=(
            False, {"ok": False, "message": "Wrong password"}
        )):
            ok, msg = mock_api.login("admin", "wrong")
            assert ok is False
            assert "Wrong password" in msg


class TestApiClientLogout:
    def test_logout_clears_state(self, mock_api):
        mock_api.logout()
        assert mock_api.token is None
        assert mock_api.username is None
        assert mock_api.role is None
        assert mock_api.is_logged_in is False


class TestApiClientThreadSafety:
    def test_lock_exists(self):
        from utils.api import ApiClient
        client = ApiClient()
        assert hasattr(client, "_lock")

    def test_concurrent_login_logout(self, mock_api):
        """Không crash khi login/logout đồng thời."""
        import threading

        def login_loop():
            for _ in range(50):
                with mock_api._lock:
                    mock_api._token = "test"
                    mock_api._username = "user"

        def logout_loop():
            for _ in range(50):
                mock_api.logout()

        t1 = threading.Thread(target=login_loop)
        t2 = threading.Thread(target=logout_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        # Không crash = pass
