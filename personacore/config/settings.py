"""Persistent application settings stored in ~/.personacore2/settings.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import platformdirs

APP_NAME = "PersonaCore2"
APP_AUTHOR = "PersonaCore"

_DEFAULTS: dict[str, Any] = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "default_model": "",
        "timeout": 120,
        "system_prompt_preset": "director",
    },
    "video": {
        "backend": "demo",  # demo | zeroscope | animatediff | custom
        "resolution": "512x512",
        "fps": 8,
        "duration_seconds": 3,
        "guidance_scale": 7.5,
        "num_inference_steps": 25,
        "seed": -1,
        "use_gpu": True,
        "gpu_memory_budget_gb": 6.0,
    },
    "ui": {
        "theme": "dark_cinema",
        "font_scale": 1.0,
        "panel_sizes": {},
        "window_geometry": None,
        "sidebar_expanded": True,
        "log_console_expanded": True,
    },
    "project": {
        "last_project": "",
        "auto_save": True,
        "auto_save_interval_s": 60,
    },
    "export": {
        "default_format": "mp4",
        "default_path": "",
        "crf": 23,
    },
    "style_preset": "cinematic",
    "personas": [],
    "first_launch": True,
}


class Settings:
    """Persistent settings with nested attribute access and JSON storage."""

    _instance: Settings | None = None

    def __new__(cls) -> Settings:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._dir = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "settings.json"
        self._data: dict[str, Any] = {}
        self.load()

    @property
    def config_dir(self) -> Path:
        return self._dir

    @property
    def projects_dir(self) -> Path:
        d = self._dir / "projects"
        d.mkdir(exist_ok=True)
        return d

    @property
    def personas_dir(self) -> Path:
        d = self._dir / "personas"
        d.mkdir(exist_ok=True)
        return d

    @property
    def cache_dir(self) -> Path:
        d = self._dir / "cache"
        d.mkdir(exist_ok=True)
        return d

    def load(self) -> None:
        data = _deep_copy(_DEFAULTS)
        if self._path.exists():
            try:
                with self._path.open(encoding="utf-8") as f:
                    saved = json.load(f)
                _deep_merge(data, saved)
            except Exception:  # noqa: BLE001
                pass
        self._data = data

    def save(self) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, *keys: str, default: Any = None) -> Any:
        obj = self._data
        for k in keys:
            if not isinstance(obj, dict):
                return default
            obj = obj.get(k, default)
        return obj

    def set(self, *keys_and_value: Any) -> None:
        *keys, value = keys_and_value
        obj = self._data
        for k in keys[:-1]:
            obj = obj.setdefault(k, {})
        obj[keys[-1]] = value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def as_dict(self) -> dict[str, Any]:
        return _deep_copy(self._data)


def _deep_copy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(v) for v in obj]
    return obj


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
