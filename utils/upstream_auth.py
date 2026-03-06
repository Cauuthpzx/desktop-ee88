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
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import json
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_CAPTCHA_ATTEMPTS = 10
CAPTCHA_RETRY_DELAY = 0.5  # seconds
DEFAULT_TIMEOUT = 30

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Path to captcha solver script
if getattr(sys, "frozen", False):
    _SCRIPT_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    _SCRIPT_DIR = Path(__file__).resolve().parent.parent

_SOLVE_SCRIPT = _SCRIPT_DIR / "scripts" / "solve-captcha.py"


def _extract_phpsessid(headers: dict[str, str]) -> str | None:
    """Extract PHPSESSID from Set-Cookie header."""
    cookie_header = headers.get("set-cookie", headers.get("Set-Cookie", ""))
    if not cookie_header:
        return None
    match = re.search(r"PHPSESSID=([^;]+)", cookie_header)
    return match.group(1) if match else None


def _fetch_raw(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[int, dict[str, str], bytes]:
    """
    Raw HTTP fetch. Returns (status, headers_dict, body_bytes).
    """
    req_headers = headers or {}
    data = body.encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        resp_headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status, resp_headers, resp.read()
    except urllib.error.HTTPError as e:
        resp_headers = {k.lower(): v for k, v in e.headers.items()}
        return e.code, resp_headers, e.read()


def _solve_captcha(image_data: bytes) -> str | None:
    """
    Solve captcha image using ddddocr via Python subprocess.
    Returns 4-char captcha code or None on failure.
    """
    if not _SOLVE_SCRIPT.exists():
        logger.error("Captcha solver script not found: %s", _SOLVE_SCRIPT)
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(_SOLVE_SCRIPT)],
            input=image_data,
            capture_output=True,
            timeout=15,
        )
        if result.returncode != 0:
            logger.warning("ddddocr failed: %s", result.stderr.decode()[:200])
            return None

        code = result.stdout.decode().strip()
        if not code or len(code) < 3 or len(code) > 6:
            logger.warning("ddddocr result invalid: %r", code)
            return None

        return code[:4]
    except subprocess.TimeoutExpired:
        logger.warning("Captcha solver timed out")
        return None
    except Exception as e:
        logger.error("Captcha solver error: %s", e)
        return None


def _rsa_encrypt(password: str, public_key_pem: str) -> str:
    """RSA-encrypt password with upstream's public key."""
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        pub_key = serialization.load_pem_public_key(public_key_pem.encode())
        encrypted = pub_key.encrypt(
            password.encode("utf-8"),
            padding.PKCS1v15(),
        )
        return base64.b64encode(encrypted).decode()
    except ImportError:
        logger.error("cryptography package required for RSA encryption")
        raise
    except Exception as e:
        logger.error("RSA encryption failed: %s", e)
        raise


def login_upstream(
    username: str,
    password: str,
    base_url: str,
) -> dict:
    """
    Login to upstream EE88 platform.

    Args:
        username: Agent upstream username
        password: Agent upstream password (plaintext)
        base_url: Upstream base URL (e.g. https://a2u4k.ee88dly.com)

    Returns:
        {
            "success": bool,
            "session_id": str | None,  # PHPSESSID on success
            "captcha_attempts": int,
            "error": str | None,
        }
    """
    base_url = base_url.rstrip("/")

    # Step 1: POST /agent/login?scene=init → get RSA public key + PHPSESSID
    init_url = f"{base_url}/agent/login?scene=init"
    init_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": DEFAULT_USER_AGENT,
    }

    status, resp_headers, resp_body = _fetch_raw(
        init_url, method="POST", headers=init_headers,
    )

    try:
        init_data = json.loads(resp_body)
    except (json.JSONDecodeError, ValueError):
        return {
            "success": False, "session_id": None,
            "captcha_attempts": 0,
            "error": f"Init response invalid: {resp_body[:200]}",
        }

    public_key = (init_data.get("data") or {}).get("public_key")
    if not public_key:
        return {
            "success": False, "session_id": None,
            "captcha_attempts": 0,
            "error": "Cannot get RSA public key from upstream",
        }

    session_id = _extract_phpsessid(resp_headers)

    # Step 2: Captcha loop
    for attempt in range(1, MAX_CAPTCHA_ATTEMPTS + 1):
        if attempt > 1:
            time.sleep(CAPTCHA_RETRY_DELAY)

        # Fetch captcha image
        captcha_url = f"{base_url}/agent/captcha?t={int(time.time() * 1000)}"
        cap_headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
        if session_id:
            cap_headers["Cookie"] = f"PHPSESSID={session_id}"

        _, cap_resp_headers, cap_image = _fetch_raw(
            captcha_url, headers=cap_headers,
        )

        new_session = _extract_phpsessid(cap_resp_headers)
        if new_session:
            session_id = new_session

        # OCR solve
        captcha_code = _solve_captcha(cap_image)
        if not captcha_code:
            logger.warning("OCR failed attempt %d, retrying...", attempt)
            continue

        # RSA encrypt password
        try:
            encrypted_password = _rsa_encrypt(password, public_key)
        except Exception as e:
            return {
                "success": False, "session_id": None,
                "captcha_attempts": attempt,
                "error": f"RSA encryption failed: {e}",
            }

        # POST /agent/login with credentials
        login_url = f"{base_url}/agent/login"
        login_body = "&".join([
            f"username={urllib.parse.quote(username)}",
            f"password={urllib.parse.quote(encrypted_password)}",
            f"captcha={urllib.parse.quote(captcha_code)}",
            "scene=login",
        ])

        login_headers: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": DEFAULT_USER_AGENT,
        }
        if session_id:
            login_headers["Cookie"] = f"PHPSESSID={session_id}"

        _, login_resp_headers, login_body_bytes = _fetch_raw(
            login_url, method="POST", headers=login_headers, body=login_body,
        )

        login_session = _extract_phpsessid(login_resp_headers)
        if login_session:
            session_id = login_session

        try:
            login_data = json.loads(login_body_bytes)
        except (json.JSONDecodeError, ValueError):
            return {
                "success": False, "session_id": None,
                "captcha_attempts": attempt,
                "error": f"Login response invalid: {login_body_bytes[:200]}",
            }

        msg = (login_data.get("msg") or "").lower()

        # Success
        if "thành công" in msg or "success" in msg:
            logger.info("Upstream login OK, attempts=%d", attempt)
            return {
                "success": True,
                "session_id": session_id,
                "captcha_attempts": attempt,
                "error": None,
            }

        # Captcha wrong → retry
        if "xác nhận" in msg or "验证码" in msg or "captcha" in msg:
            logger.warning("Captcha wrong attempt %d: %s", attempt, login_data.get("msg"))
            continue

        # Password wrong → stop
        if "mật khẩu" in msg or "密码" in msg or "password" in msg:
            return {
                "success": False, "session_id": None,
                "captcha_attempts": attempt,
                "error": f"Wrong password: {login_data.get('msg')}",
            }

        # Other error → stop
        return {
            "success": False, "session_id": None,
            "captcha_attempts": attempt,
            "error": f"Login error: {login_data.get('msg', 'Unknown')}",
        }

    # Exhausted all attempts
    return {
        "success": False, "session_id": None,
        "captcha_attempts": MAX_CAPTCHA_ATTEMPTS,
        "error": f"Captcha solving failed after {MAX_CAPTCHA_ATTEMPTS} attempts",
    }


def check_session(session_id: str, base_url: str) -> bool:
    """
    Check if upstream session is still valid by fetching user list (limit=1).
    Returns True if session is valid.
    """
    base_url = base_url.rstrip("/")
    url = f"{base_url}/agent/user.html"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": DEFAULT_USER_AGENT,
        "Cookie": f"PHPSESSID={session_id}",
    }
    body = "page=1&limit=1"

    try:
        status, _, resp_body = _fetch_raw(
            url, method="POST", headers=headers, body=body, timeout=15,
        )
        if status != 200:
            return False
        data = json.loads(resp_body)
        return data.get("code") in (0, 1)
    except Exception:
        return False


def logout_upstream(session_id: str, base_url: str) -> None:
    """Logout from upstream (best-effort)."""
    base_url = base_url.rstrip("/")
    try:
        _fetch_raw(
            f"{base_url}/agent/loginOut",
            headers={
                "Cookie": f"PHPSESSID={session_id}",
                "User-Agent": DEFAULT_USER_AGENT,
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=10,
        )
    except Exception:
        pass
