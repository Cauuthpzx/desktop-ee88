"""
utils/upstream_auth.py — EE88 upstream login engine.

Port from MAXHUB backend login-engine.ts + captcha-solver.ts.
Handles automated login to upstream EE88 platform with captcha OCR solving.

Usage:
    from utils.upstream_auth import login_upstream, check_session

    result = login_upstream(username, password, base_url)
    # result: {"success": True, "session_id": "...", "captcha_attempts": 3}
"""
from __future__ import annotations

import logging
import re
import time
import threading
from typing import Any

import requests

logger = logging.getLogger(__name__)

MAX_CAPTCHA_ATTEMPTS = 10
CAPTCHA_RETRY_DELAY = 0.5  # seconds
DEFAULT_TIMEOUT = 30

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "X-Requested-With": "XMLHttpRequest",
}

# ── Login Lock ───────────────────────────────────────────────
# Prevent concurrent login attempts for the same agent
_login_locks: dict[str, float] = {}
_lock_mutex = threading.Lock()
_LOCK_TIMEOUT = 300  # 5 minutes


def _acquire_lock(agent_key: str) -> bool:
    """Acquire login lock for agent. Returns False if already locked."""
    with _lock_mutex:
        now = time.time()
        lock_time = _login_locks.get(agent_key)
        if lock_time and now - lock_time < _LOCK_TIMEOUT:
            return False
        _login_locks[agent_key] = now
        return True


def _release_lock(agent_key: str) -> None:
    """Release login lock for agent."""
    with _lock_mutex:
        _login_locks.pop(agent_key, None)


# ── Captcha Solver ───────────────────────────────────────────
# Character confusion fixes (common OCR mistakes for numeric captchas)
_CHAR_FIX = {
    "o": "0", "O": "0",
    "l": "1", "I": "1",
    "z": "2", "Z": "2",
    "s": "5", "S": "5",
    "b": "6",
    "B": "8",
    "g": "9", "q": "9",
}

# Lazy-loaded OCR instance (ddddocr is heavy to import)
_ocr_instance = None
_ocr_lock = threading.Lock()


def _get_ocr():
    """Get or create ddddocr instance (thread-safe singleton)."""
    global _ocr_instance
    if _ocr_instance is None:
        with _ocr_lock:
            if _ocr_instance is None:
                try:
                    import ddddocr
                    _ocr_instance = ddddocr.DdddOcr(show_ad=False)
                    logger.info("ddddocr OCR engine initialized")
                except ImportError:
                    logger.error("ddddocr not installed: pip install ddddocr")
                    raise
    return _ocr_instance


def _solve_captcha(image_data: bytes) -> str | None:
    """
    Solve captcha image using ddddocr directly.
    Returns 4-char captcha code or None on failure.
    """
    try:
        ocr = _get_ocr()
        result = ocr.classification(image_data)

        if not result:
            return None

        # Apply character fixes (captchas are typically numeric)
        cleaned = "".join(_CHAR_FIX.get(c, c) for c in result)
        # Only keep alphanumeric
        cleaned = "".join(c for c in cleaned if c.isalnum())

        if len(cleaned) < 3 or len(cleaned) > 6:
            logger.warning("OCR result invalid length: %r -> %r", result, cleaned)
            return None

        return cleaned[:4]
    except Exception as e:
        logger.error("Captcha solver error: %s", e)
        return None


# ── RSA Encryption ───────────────────────────────────────────
def _rsa_encrypt(password: str, public_key_pem: str) -> str:
    """RSA-encrypt password with upstream's public key (PKCS1v15 padding)."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        pub_key = serialization.load_pem_public_key(public_key_pem.encode())
        encrypted = pub_key.encrypt(
            password.encode("utf-8"),
            padding.PKCS1v15(),
        )
        return base64.b64encode(encrypted).decode()
    except ImportError:
        logger.error("cryptography package required: pip install cryptography")
        raise
    except Exception as e:
        logger.error("RSA encryption failed: %s", e)
        raise


# ── HTTP Session Helper ──────────────────────────────────────
def _extract_phpsessid(response: requests.Response) -> str | None:
    """Extract PHPSESSID from response cookies."""
    session_id = response.cookies.get("PHPSESSID")
    if session_id:
        return session_id
    # Fallback: parse Set-Cookie header manually
    for val in response.headers.get("Set-Cookie", "").split(","):
        match = re.search(r"PHPSESSID=([^;]+)", val)
        if match:
            return match.group(1)
    return None


def _make_result(
    success: bool,
    session_id: str | None = None,
    captcha_attempts: int = 0,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "success": success,
        "session_id": session_id,
        "captcha_attempts": captcha_attempts,
        "error": error,
    }


# ── Main Login Flow ──────────────────────────────────────────
def login_upstream(
    username: str,
    password: str,
    base_url: str,
) -> dict[str, Any]:
    """
    Login to upstream EE88 platform.

    Flow: init (RSA key) → captcha loop (OCR + submit) → session cookie

    Returns:
        {
            "success": bool,
            "session_id": str | None,
            "captcha_attempts": int,
            "error": str | None,
        }
    """
    base_url = base_url.rstrip("/")
    agent_key = f"{username}@{base_url}"

    # Acquire login lock
    if not _acquire_lock(agent_key):
        return _make_result(
            False, error="Agent is already logging in (concurrent lock).",
        )

    try:
        return _login_flow(username, password, base_url)
    finally:
        _release_lock(agent_key)


def _login_flow(username: str, password: str, base_url: str) -> dict[str, Any]:
    """Internal login flow (called with lock held)."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    session.verify = False  # Some upstream certs may be self-signed

    # Suppress InsecureRequestWarning
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # ── Step 1: INIT — get RSA public key + PHPSESSID ────────
    init_url = f"{base_url}/agent/login?scene=init"

    try:
        resp = session.post(
            init_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as e:
        return _make_result(False, error=f"Init request failed: {e}")

    try:
        init_data = resp.json()
    except ValueError:
        return _make_result(
            False, error=f"Init response invalid: {resp.text[:200]}",
        )

    public_key = (init_data.get("data") or {}).get("public_key")
    if not public_key:
        return _make_result(
            False, error="Cannot get RSA public key from upstream",
        )

    # Session cookies are managed automatically by requests.Session
    logger.info("Init OK, got RSA key, PHPSESSID=%s", session.cookies.get("PHPSESSID"))

    # ── Step 2: Captcha loop ─────────────────────────────────
    for attempt in range(1, MAX_CAPTCHA_ATTEMPTS + 1):
        if attempt > 1:
            time.sleep(CAPTCHA_RETRY_DELAY)

        # Fetch captcha image
        captcha_url = f"{base_url}/agent/captcha?t={int(time.time() * 1000)}"
        try:
            cap_resp = session.get(captcha_url, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as e:
            logger.warning("Captcha fetch failed attempt %d: %s", attempt, e)
            continue

        cap_image = cap_resp.content
        if not cap_image or len(cap_image) < 100:
            logger.warning("Captcha image too small (%d bytes), retrying", len(cap_image))
            continue

        # OCR solve
        captcha_code = _solve_captcha(cap_image)
        if not captcha_code:
            logger.warning("OCR failed attempt %d, retrying...", attempt)
            continue

        logger.debug("Captcha attempt %d: OCR=%s", attempt, captcha_code)

        # RSA encrypt password
        try:
            encrypted_password = _rsa_encrypt(password, public_key)
        except Exception as e:
            return _make_result(
                False, captcha_attempts=attempt,
                error=f"RSA encryption failed: {e}",
            )

        # POST /agent/login with credentials
        login_url = f"{base_url}/agent/login"
        login_data = {
            "username": username,
            "password": encrypted_password,
            "captcha": captcha_code,
            "scene": "login",
        }

        try:
            login_resp = session.post(
                login_url,
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=DEFAULT_TIMEOUT,
            )
        except requests.RequestException as e:
            return _make_result(
                False, captcha_attempts=attempt,
                error=f"Login request failed: {e}",
            )

        try:
            login_result = login_resp.json()
        except ValueError:
            return _make_result(
                False, captcha_attempts=attempt,
                error=f"Login response invalid: {login_resp.text[:200]}",
            )

        msg = (login_result.get("msg") or "").lower()

        # Success
        if "thành công" in msg or "success" in msg:
            final_session = session.cookies.get("PHPSESSID")
            logger.info(
                "Upstream login OK for %s, attempts=%d, session=%s",
                username, attempt, final_session[:8] if final_session else "?",
            )
            return _make_result(
                True, session_id=final_session, captcha_attempts=attempt,
            )

        # Captcha wrong → retry
        if "xác nhận" in msg or "验证码" in msg or "captcha" in msg:
            logger.warning(
                "Captcha wrong attempt %d: %s", attempt, login_result.get("msg"),
            )
            continue

        # Password wrong → stop
        if "mật khẩu" in msg or "密码" in msg or "password" in msg:
            return _make_result(
                False, captcha_attempts=attempt,
                error=f"Wrong password: {login_result.get('msg')}",
            )

        # Other error → stop
        return _make_result(
            False, captcha_attempts=attempt,
            error=f"Login error: {login_result.get('msg', 'Unknown')}",
        )

    # Exhausted all attempts
    return _make_result(
        False,
        captcha_attempts=MAX_CAPTCHA_ATTEMPTS,
        error=f"Captcha solving failed after {MAX_CAPTCHA_ATTEMPTS} attempts",
    )


# ── Session Check ────────────────────────────────────────────
def check_session(session_id: str, base_url: str) -> bool:
    """
    Check if upstream session is still valid.
    Calls /agent/user.html with limit=1 — if it returns data, session is valid.
    """
    base_url = base_url.rstrip("/")
    url = f"{base_url}/agent/user.html"

    try:
        resp = requests.post(
            url,
            data="page=1&limit=1",
            headers={
                **DEFAULT_HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": f"PHPSESSID={session_id}",
            },
            timeout=15,
            verify=False,
        )
        if resp.status_code != 200:
            return False
        data = resp.json()
        return data.get("code") in (0, 1)
    except Exception:
        return False


# ── Logout ───────────────────────────────────────────────────
def logout_upstream(session_id: str, base_url: str) -> None:
    """Logout from upstream (best-effort)."""
    base_url = base_url.rstrip("/")
    try:
        requests.get(
            f"{base_url}/agent/loginOut",
            headers={
                **DEFAULT_HEADERS,
                "Cookie": f"PHPSESSID={session_id}",
            },
            timeout=10,
            verify=False,
        )
    except Exception:
        pass
