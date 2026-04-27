"""QThread worker for refreshing Ollama model list."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from personacore.ai.ollama_client import OllamaClient, OllamaError
from personacore.logging_module import get_logger

log = get_logger("workers.models")


class ModelRefreshWorker(QThread):
    models_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    ollama_status = pyqtSignal(bool)  # True = alive

    def __init__(self, client: OllamaClient) -> None:
        super().__init__()
        self._client = client

    def run(self) -> None:
        alive = self._client.is_alive()
        self.ollama_status.emit(alive)
        if not alive:
            self.error_occurred.emit("Cannot connect to Ollama at " + self._client.base_url)
            return
        try:
            models = self._client.list_models()
            self.models_loaded.emit(models)
        except OllamaError as e:
            self.error_occurred.emit(str(e))
