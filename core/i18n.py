"""
core/i18n.py — Internationalization (i18n) module.

Support 3 languages: Vietnamese (vi), English (en), Chinese (zh).
Default language: Vietnamese.

Usage:
    from core.i18n import t, set_language, get_language

    # Get translated text:
    label = t("login.title")          # "Dang nhap" / "Login" / "登录"
    msg = t("login.error.required", field="Username")  # with parameters

    # Switch language:
    set_language("en")

    # Get current language:
    lang = get_language()             # "vi" | "en" | "zh"

Translation files: i18n/vi.json, i18n/en.json, i18n/zh.json
Keys use dot notation: "section.subsection.key"
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal
from utils.settings import settings

logger = logging.getLogger(__name__)


class _I18nSignals(QObject):
    """Signal emitter for language changes."""
    language_changed = pyqtSignal(str)  # lang code


i18n_signals = _I18nSignals()

# Supported languages
LANGUAGES = {
    "vi": "Tiếng Việt",
    "en": "English",
    "zh": "中文",
}
DEFAULT_LANG = "vi"

if getattr(sys, "frozen", False):
    _I18N_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "i18n"
else:
    _I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
_translations: dict[str, dict[str, Any]] = {}
_current_lang: str = DEFAULT_LANG


def _load_language(lang: str) -> dict[str, Any]:
    """Load a language JSON file. Returns flat dict or empty dict on error."""
    if lang in _translations:
        return _translations[lang]

    filepath = _I18N_DIR / f"{lang}.json"
    if not filepath.exists():
        logger.warning("Language file not found: %s", filepath)
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _translations[lang] = data
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load language file %s: %s", filepath, e)
        return {}


def _resolve(data: dict[str, Any], key: str) -> str | None:
    """Resolve dot-notation key from nested dict."""
    parts = key.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current if isinstance(current, str) else None


def t(key: str, **kwargs: Any) -> str:
    """Get translated string by key.

    Args:
        key: Dot-notation key, e.g. "login.title"
        **kwargs: Format parameters, e.g. t("error.required", field="Name")

    Returns:
        Translated string, or the key itself if not found.
    """
    data = _load_language(_current_lang)
    text = _resolve(data, key)

    # Fallback to default language
    if text is None and _current_lang != DEFAULT_LANG:
        data = _load_language(DEFAULT_LANG)
        text = _resolve(data, key)

    # Fallback to key itself
    if text is None:
        logger.debug("Missing translation: [%s] %s", _current_lang, key)
        return key

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text

    return text


def set_language(lang: str) -> None:
    """Switch current language. Saves preference and emits language_changed signal."""
    global _current_lang
    if lang not in LANGUAGES:
        logger.warning("Unsupported language: %s", lang)
        return
    if lang == _current_lang:
        return
    _current_lang = lang
    settings.set("app/language", lang)
    _load_language(lang)
    i18n_signals.language_changed.emit(lang)


def get_language() -> str:
    """Get current language code."""
    return _current_lang


def get_languages() -> dict[str, str]:
    """Get all supported languages as {code: display_name}."""
    return dict(LANGUAGES)


def init() -> None:
    """Initialize i18n — load saved language preference."""
    global _current_lang
    saved = settings.get_str("app/language", DEFAULT_LANG)
    if saved in LANGUAGES:
        _current_lang = saved
    _load_language(_current_lang)


def reload() -> None:
    """Clear cache and reload current language."""
    _translations.clear()
    _load_language(_current_lang)
