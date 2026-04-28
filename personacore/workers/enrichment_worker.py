"""QThread worker for streaming Ollama prompt enrichment."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from personacore.ai.ollama_client import OllamaClient, OllamaError
from personacore.ai.personas import Persona
from personacore.ai.prompt_enricher import PromptEnricher
from personacore.logging_module import get_logger

log = get_logger("workers.enrichment")


class EnrichmentWorker(QThread):
    """Streams Ollama enrichment in a background thread."""

    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)        # full enriched text
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(float, str)

    def __init__(
        self,
        client: OllamaClient,
        raw_prompt: str,
        model: str,
        persona: Persona,
    ) -> None:
        super().__init__()
        self._client = client
        self._raw_prompt = raw_prompt
        self._model = model
        self._persona = persona
        self._cancelled = [False]
        self._enricher = PromptEnricher(client)

    def cancel(self) -> None:
        self._cancelled[0] = True

    def run(self) -> None:
        log.info("Starting enrichment: model=%s", self._model)
        self.progress.emit(0.0, "Connecting to Ollama...")
        full_text = []
        try:
            for chunk in self._enricher.enrich_stream(
                self._raw_prompt,
                self._model,
                self._persona,
                self._cancelled,
            ):
                if self._cancelled[0]:
                    return
                full_text.append(chunk)
                self.chunk_received.emit(chunk)

            result = "".join(full_text)
            self.progress.emit(1.0, "Enrichment complete")
            self.finished.emit(result)

        except OllamaError as e:
            log.error("Enrichment error: %s", e)
            self.error_occurred.emit(str(e))
