"""
Custom mocks cho tests.
"""
from __future__ import annotations
from unittest.mock import MagicMock


class MockDatabase:
    """Mock database connection cho tests không cần PostgreSQL."""

    def __init__(self):
        self._data: dict[str, list[dict]] = {}
        self._cursor = MagicMock()
        self._cursor.fetchone.return_value = None
        self._cursor.fetchall.return_value = []
        self._cursor.rowcount = 0
        self.autocommit = True

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    def set_fetchone(self, data: dict | None):
        """Set response cho next fetchone()."""
        self._cursor.fetchone.return_value = data

    def set_fetchall(self, data: list[dict]):
        """Set response cho next fetchall()."""
        self._cursor.fetchall.return_value = data


class MockApiResponse:
    """Mock HTTP response cho ApiClient tests."""

    def __init__(self, data: dict, status_code: int = 200):
        self.data = data
        self.status_code = status_code
        self._body = __import__("json").dumps(data).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
