"""Ustawienia aplikacji zapisywane w katalogu uzytkownika."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

APP_DIR_NAME = "LyricsManagerPro"

DEFAULTS: dict[str, Any] = {
    "ui_language": "pl",
    "text_language": "pl",
    "ai_output_language": "pl",
    "theme": "dark",                     # light | dark | system
    "color_theme": "blue",
    "editor_font_family": "Consolas",
    "editor_font_size": 14,
    "show_syllable_gutter": True,
    "live_analysis": True,
    "ai_engine": "ollama",               # ollama | openrouter
    "openrouter_api_key": "",
    "openrouter_model": "anthropic/claude-sonnet-4.5",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.1",
    "ai_temperature": 0.8,
    "history_autosave_minutes": 5,
    "export_autotag": True,
    "export_include_meta": True,
    "repetition_min_count": 2,
    "repetition_ignore_stopwords": True,
    "highlight_rhymes": True,
    "spell_check_enabled": True,
    "spell_dict_pl": "",
    "spell_dict_en": "",
    "last_directory": "",
    "window_geometry": "1360x860",
}


def data_dir() -> Path:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = Path(base) / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return data_dir() / "settings.json"


def _obfuscate(value: str) -> str:
    """Lekkie zaciemnienie klucza API - chroni przed przypadkowym podejrzeniem,
    nie jest szyfrowaniem. Klucz i tak lezy na dysku uzytkownika."""
    if not value:
        return ""
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _deobfuscate(value: str) -> str:
    if not value:
        return ""
    try:
        return base64.b64decode(value.encode("ascii")).decode("utf-8")
    except Exception:
        return ""


_SECRET_KEYS = {"openrouter_api_key"}


class Config:
    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        path = config_path()
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        for key, value in raw.items():
            if key in _SECRET_KEYS:
                self._data[key] = _deobfuscate(value)
            elif key in DEFAULTS:
                self._data[key] = value

    def save(self) -> None:
        out: dict[str, Any] = {}
        for key, value in self._data.items():
            out[key] = _obfuscate(value) if key in _SECRET_KEYS else value
        try:
            config_path().write_text(
                json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, values: dict[str, Any]) -> None:
        self._data.update(values)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)
