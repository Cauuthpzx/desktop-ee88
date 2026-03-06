"""
utils/upstream_auth.py — EE88 upstream login engine.

Port from EE88-SyncTool login_service.py + MAXHUB login-engine.ts.

Login flow:
1. POST /agent/login {scene: 'init'} → get public_key, captcha_url
2. GET captcha_url → captcha image
3. ddddocr solve captcha (raw + preprocessed, pick best)
4. RSA encrypt password with public_key (PKCS1v15)
5. POST /agent/login {username, password: encrypted, captcha, scene: 'login'}
6. Response: {code: 1, msg, url} = success

Key design:
- Fresh session per login attempt (avoid stale cookie jar)
- Dual captcha OCR: raw + preprocessed, pick result with more digits
- Merge cookies from session jar + Set-Cookie headers
- Login lock prevents concurrent login for same agent
- check_cookies_live with redirect detection
"""
from __future__ import annotations

import logging
import re
import time
import threading
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from core.i18n import t
except ImportError:
    # Server-side fallback (no PyQt6)
    def t(key: str, **kwargs: Any) -> str:  # type: ignore[misc]
        return key

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
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
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
# Extended char map from EE88-SyncTool (covers more OCR confusion cases)
_OCR_CHAR_MAP: dict[str, str] = {
    "o": "0", "O": "0", "D": "0", "Q": "0", "\u53e3": "0",
    "l": "1", "I": "1", "i": "1", "|": "1",
    "z": "2", "Z": "2",
    "e": "3", "E": "3",
    "A": "4", "a": "4",
    "s": "5", "S": "5",
    "b": "6", "G": "6",
    "T": "7", "t": "7",
    "B": "8",
    "g": "9", "q": "9", "p": "9", "P": "9",
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


def _clean_ocr(raw: str) -> str:
    """Clean OCR result — map confused chars to digits, keep alnum ASCII."""
    cleaned = ""
    for c in raw:
        if c.isdigit() and c.isascii():
            cleaned += c
        elif c in _OCR_CHAR_MAP:
            cleaned += _OCR_CHAR_MAP[c]
        elif c.isascii() and c.isalnum():
            cleaned += c
    return cleaned


def _preprocess_image(image_bytes: bytes) -> bytes:
    """Preprocess captcha: grayscale + upscale + contrast + sharpen."""
    try:
        import io
        from PIL import Image, ImageEnhance, ImageFilter

        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        w, h = img.size
        if w < 120:
            img = img.resize((w * 2, h * 2), Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = img.filter(ImageFilter.SHARPEN)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return image_bytes


def _solve_captcha(image_data: bytes) -> str | None:
    """
    Solve captcha with dual OCR: raw + preprocessed image.
    Picks result with more digit characters for better accuracy.
    Returns 4-char code or None on failure.
    """
    try:
        ocr = _get_ocr()

        # Try raw image
        raw1 = ocr.classification(image_data)
        cleaned1 = _clean_ocr(raw1)

        # Try preprocessed image (grayscale + contrast + sharpen)
        processed = _preprocess_image(image_data)
        raw2 = ocr.classification(processed)
        cleaned2 = _clean_ocr(raw2)

        # Pick result with more digit chars (captchas are numeric)
        digits1 = sum(1 for c in cleaned1 if c.isdigit())
        digits2 = sum(1 for c in cleaned2 if c.isdigit())
        cleaned = cleaned1 if digits1 >= digits2 else cleaned2

        if not cleaned:
            logger.warning("OCR returned empty: raw1=%r, raw2=%r", raw1, raw2)
            return None

        logger.info(
            "Captcha OCR: raw1=%s->%s, raw2=%s->%s, picked=%s",
            raw1, cleaned1, raw2, cleaned2, cleaned,
        )

        if len(cleaned) < 3 or len(cleaned) > 6:
            logger.warning("OCR result invalid length: %r", cleaned)
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

        # Normalize PEM format (upstream may return messy PEM)
        key_data = public_key_pem
        key_data = key_data.replace("-----BEGIN PUBLIC KEY-----", "")
        key_data = key_data.replace("-----END PUBLIC KEY-----", "")
        key_data = key_data.replace("\n", "").replace("\r", "").strip()

        lines = [key_data[i:i + 64] for i in range(0, len(key_data), 64)]
        pem_formatted = (
            "-----BEGIN PUBLIC KEY-----\n"
            + "\n".join(lines)
            + "\n-----END PUBLIC KEY-----"
        )

        pub_key = serialization.load_pem_public_key(pem_formatted.encode())
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


# ── HTTP Session Factory ─────────────────────────────────────
def _create_session() -> requests.Session:
    """Create HTTP session with retry strategy."""
    session = requests.Session()

    retry_strategy = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=5, pool_maxsize=5)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    session.verify = False

    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return session


def _extract_response_cookies(response: requests.Response) -> dict[str, str]:
    """Extract cookies from Set-Cookie headers (not just session jar)."""
    cookies: dict[str, str] = {}
    for raw in response.headers.get("Set-Cookie", "").split(","):
        part = raw.split(";", 1)[0].strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


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

    Flow: init (RSA key + captcha URL) → captcha loop (dual OCR + submit) → session cookie

    Returns:
        {"success": bool, "session_id": str|None, "captcha_attempts": int, "error": str|None}
    """
    base_url = base_url.rstrip("/")
    agent_key = f"{username}@{base_url}"

    if not _acquire_lock(agent_key):
        return _make_result(False, error=t("upstream.concurrent_lock"))

    try:
        return _login_flow(username, password, base_url)
    finally:
        _release_lock(agent_key)


def _login_flow(username: str, password: str, base_url: str) -> dict[str, Any]:
    """Internal login flow with per-attempt fresh session."""
    login_url = f"{base_url}/agent/login"

    for attempt in range(1, MAX_CAPTCHA_ATTEMPTS + 1):
        if attempt > 1:
            time.sleep(CAPTCHA_RETRY_DELAY)

        # Fresh session each attempt (clear cookie jar to avoid conflicts)
        session = _create_session()

        try:
            result = _single_attempt(session, username, password, base_url, login_url, attempt)
        except Exception as e:
            logger.error("Attempt %d unexpected error: %s", attempt, e)
            session.close()
            continue

        if result is None:
            # OCR/fetch failed, retry
            session.close()
            continue

        if result.get("success"):
            return result

        if result.pop("_retry", False):
            # Captcha wrong or unknown, retry
            session.close()
            continue

        # Non-retryable error (wrong password, account error, etc.)
        session.close()
        return result

    return _make_result(
        False,
        captcha_attempts=MAX_CAPTCHA_ATTEMPTS,
        error=t("upstream.captcha_exhausted", n=MAX_CAPTCHA_ATTEMPTS),
    )


def _single_attempt(
    session: requests.Session,
    username: str,
    password: str,
    base_url: str,
    login_url: str,
    attempt: int,
) -> dict[str, Any] | None:
    """Single login attempt: init → captcha → login. Returns result or None (retry)."""
    logger.info("Login attempt %d/%d for %s", attempt, MAX_CAPTCHA_ATTEMPTS, username)

    # ── Step 1: INIT — get RSA public key + captcha URL ──────
    try:
        resp = session.post(
            login_url,
            json={"scene": "init"},
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as e:
        logger.warning("Init failed attempt %d: %s", attempt, e)
        return None

    try:
        init_data = resp.json()
    except ValueError:
        logger.warning("Init response invalid: %s", resp.text[:200])
        return None

    data = init_data.get("data") or {}
    public_key = data.get("public_key")
    captcha_url_path = data.get("captcha_url", "")

    if not public_key:
        return _make_result(False, captcha_attempts=attempt, error=t("upstream.no_rsa_key"))

    # Build full captcha URL
    if captcha_url_path.startswith("/"):
        captcha_url = f"{base_url}{captcha_url_path}"
    elif captcha_url_path.startswith("http"):
        captcha_url = captcha_url_path
    else:
        captcha_url = f"{base_url}/agent/captcha?t={int(time.time() * 1000)}"

    logger.info("Init OK, captcha_url=%s", captcha_url)

    # ── Step 2: Fetch captcha image ──────────────────────────
    try:
        cap_resp = session.get(captcha_url, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as e:
        logger.warning("Captcha fetch failed attempt %d: %s", attempt, e)
        return None

    cap_image = cap_resp.content
    if not cap_image or len(cap_image) < 100:
        logger.warning("Captcha image too small (%d bytes)", len(cap_image) if cap_image else 0)
        return None

    # ── Step 3: Dual OCR solve ───────────────────────────────
    captcha_code = _solve_captcha(cap_image)
    if not captcha_code:
        return None

    # ── Step 4: RSA encrypt password ─────────────────────────
    try:
        encrypted_password = _rsa_encrypt(password, public_key)
    except Exception as e:
        return _make_result(
            False, captcha_attempts=attempt,
            error=t("upstream.rsa_failed", error=str(e)),
        )

    # ── Step 5: POST login ───────────────────────────────────
    login_data = {
        "username": username,
        "password": encrypted_password,
        "captcha": captcha_code,
        "scene": "login",
    }

    try:
        login_resp = session.post(
            login_url,
            json=login_data,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as e:
        return _make_result(
            False, captcha_attempts=attempt,
            error=t("upstream.login_request_failed", error=str(e)),
        )

    # ── Step 6: Parse response ───────────────────────────────
    try:
        login_result = login_resp.json()
    except ValueError:
        return _make_result(
            False, captcha_attempts=attempt,
            error=t("upstream.login_response_invalid", detail=login_resp.text[:200]),
        )

    code = login_result.get("code", -1)
    msg = login_result.get("msg") or ""
    msg_lower = msg.lower()

    # Success: code == 1 OR message contains success keywords
    if code == 1 or "thành công" in msg_lower or "success" in msg_lower:
        # Merge cookies from session jar + Set-Cookie headers
        jar_cookies = dict(session.cookies)
        resp_cookies = _extract_response_cookies(login_resp)
        all_cookies = {**jar_cookies, **resp_cookies}
        final_session = all_cookies.get("PHPSESSID") or session.cookies.get("PHPSESSID")

        logger.info(
            "Upstream login OK for %s, attempts=%d, cookies=%d, session=%s",
            username, attempt, len(all_cookies),
            final_session[:8] if final_session else "?",
        )
        return _make_result(True, session_id=final_session, captcha_attempts=attempt)

    # Captcha wrong → retry
    captcha_kw = ("captcha", "xac nhan", "xác nhận", "ma xac", "mã xác", "verify", "验证码")
    if any(kw in msg_lower for kw in captcha_kw):
        logger.warning("Captcha wrong attempt %d: %s", attempt, msg)
        return {"_retry": True, **_make_result(False, captcha_attempts=attempt)}

    # Password wrong → stop
    password_kw = ("password", "mat khau", "mật khẩu", "密码", "pwd")
    if any(kw in msg_lower for kw in password_kw):
        return _make_result(
            False, captcha_attempts=attempt,
            error=t("upstream.wrong_password", msg=msg),
        )

    # Account error → stop
    account_kw = ("account", "tai khoan", "tài khoản", "用户", "user", "khong ton tai", "không chính xác")
    if any(kw in msg_lower for kw in account_kw):
        return _make_result(
            False, captcha_attempts=attempt,
            error=t("upstream.login_error", msg=msg),
        )

    # Unknown error — retry
    if attempt < MAX_CAPTCHA_ATTEMPTS:
        logger.warning("Unknown response attempt %d: code=%s msg=%s", attempt, code, msg)
        return {"_retry": True, **_make_result(False, captcha_attempts=attempt)}

    return _make_result(
        False, captcha_attempts=attempt,
        error=t("upstream.login_error", msg=msg or f"code={code}"),
    )


# ── Session Check ────────────────────────────────────────────
def check_session(session_id: str, base_url: str) -> bool:
    """
    Check if upstream session is still valid.
    Uses POST /agent/user.html — handles redirects and various response formats.
    """
    base_url = base_url.rstrip("/")
    url = f"{base_url}/agent/user.html"

    try:
        resp = requests.post(
            url,
            data="page=1&limit=1",
            headers={
                **DEFAULT_HEADERS,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Cookie": f"PHPSESSID={session_id}",
            },
            timeout=15,
            verify=False,
            allow_redirects=False,
        )

        # 301/302 redirect to login → expired
        if resp.status_code in (301, 302):
            location = resp.headers.get("Location", "").lower()
            if "login" in location:
                return False

        if resp.status_code != 200:
            return False

        try:
            data = resp.json()
            code = data.get("code")

            # code == 0 with actual data list = valid
            if code == 0 and isinstance(data.get("data"), list):
                return True

            # code in (0, 1) = generally valid
            if code in (0, 1):
                return True

            # Check for login redirect in message
            msg_text = str(data.get("msg", "")).lower()
            if "login" in msg_text or "đăng nhập" in msg_text:
                return False

            # "jump" in data = redirect to login
            resp_data = data.get("data", {})
            if isinstance(resp_data, dict) and "jump" in resp_data:
                return False

            return True

        except ValueError:
            # Response is HTML (login page)
            text = resp.text[:200].lower()
            if "login" in text or "đăng nhập" in text:
                return False
            return True

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
