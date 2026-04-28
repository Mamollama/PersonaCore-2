"""Model management — list, select, and cache Ollama models."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from personacore.logging_module import get_logger

from .ollama_client import OllamaClient, OllamaError

log = get_logger("ai.models")


class ModelManager(QObject):
    """Maintains an up-to-date list of available Ollama models."""

    models_updated = pyqtSignal(list)   # list[dict]
    error_occurred = pyqtSignal(str)

    def __init__(self, client: OllamaClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = client
        self._models: list[dict[str, Any]] = []
        self._selected: str = ""

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)

    @property
    def models(self) -> list[dict[str, Any]]:
        return self._models

    @property
    def model_names(self) -> list[str]:
        return [m.get("name", "") for m in self._models]

    @property
    def selected_model(self) -> str:
        return self._selected

    @selected_model.setter
    def selected_model(self, name: str) -> None:
        self._selected = name
        log.info("Selected model: %s", name)

    def refresh(self) -> None:
        try:
            raw = self._client.list_models()
            self._models = raw
            if self._models and not self._selected:
                self._selected = self._models[0].get("name", "")
            self.models_updated.emit(self._models)
            log.debug("Models refreshed: %d available", len(self._models))
        except OllamaError as e:
            self.error_occurred.emit(str(e))
            log.warning("Failed to refresh models: %s", e)

    def start_auto_refresh(self, interval_ms: int = 30_000) -> None:
        self._refresh_timer.start(interval_ms)

    def stop_auto_refresh(self) -> None:
        self._refresh_timer.stop()

    def format_model_info(self, name: str) -> str:
        for m in self._models:
            if m.get("name") == name:
                size = m.get("size", 0)
                size_gb = size / (1024**3) if size else 0
                return f"{name}  ({size_gb:.1f} GB)"
        return name
