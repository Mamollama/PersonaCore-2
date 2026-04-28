"""QThread worker for video generation pipeline."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from personacore.logging_module import get_logger
from personacore.video.base_generator import BaseVideoGenerator, GenerationParams, GenerationResult

log = get_logger("workers.generation")


class GenerationWorker(QThread):
    """Runs video generation in a background thread."""

    progress = pyqtSignal(float, str)         # fraction 0..1, message
    step_changed = pyqtSignal(str)             # step name
    finished = pyqtSignal(object)              # GenerationResult
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        generator: BaseVideoGenerator,
        params: GenerationParams,
        output_dir: Path,
    ) -> None:
        super().__init__()
        self._generator = generator
        self._params = params
        self._output_dir = output_dir
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        log.info("Generation cancellation requested")

    def run(self) -> None:
        log.info("Starting generation with %s", self._generator.name)
        self.step_changed.emit("generating")
        self.progress.emit(0.0, "Initializing generator...")

        try:
            self._generator.setup()
            self.progress.emit(0.05, "Generator ready")

            result = self._generator.generate(
                params=self._params,
                output_dir=self._output_dir,
                on_progress=self._on_progress,
                is_cancelled=lambda: self._cancelled,
            )

            if self._cancelled:
                self.step_changed.emit("cancelled")
                self.finished.emit(GenerationResult(success=False, error="Cancelled by user"))
                return

            if result.success:
                self.step_changed.emit("complete")
                self.progress.emit(1.0, "Generation complete!")
            else:
                self.step_changed.emit("error")
                self.error_occurred.emit(result.error or "Generation failed")

            self.finished.emit(result)

        except Exception as e:
            log.exception("Generation exception")
            self.step_changed.emit("error")
            self.error_occurred.emit(str(e))
            self.finished.emit(GenerationResult(success=False, error=str(e)))

    def _on_progress(self, fraction: float, message: str) -> None:
        self.progress.emit(fraction, message)
