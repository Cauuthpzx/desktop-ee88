"""
Custom assertions cho tests.
"""
from __future__ import annotations


def assert_valid(result: str | None, msg: str = "") -> None:
    """Assert validator trả về None (hợp lệ)."""
    assert result is None, f"Expected valid but got error: {result}. {msg}"


def assert_invalid(result: str | None, msg: str = "") -> None:
    """Assert validator trả về error string (không hợp lệ)."""
    assert result is not None, f"Expected invalid but got None. {msg}"
    assert isinstance(result, str), f"Error should be string, got {type(result)}. {msg}"


def assert_api_ok(response: tuple[bool, dict], msg: str = "") -> dict:
    """Assert API response thành công. Trả về data dict."""
    ok, data = response
    assert ok is True, f"API call failed: {data}. {msg}"
    return data


def assert_api_fail(response: tuple[bool, dict], msg: str = "") -> dict:
    """Assert API response thất bại. Trả về data dict."""
    ok, data = response
    assert ok is False, f"API call should fail but succeeded. {msg}"
    return data
