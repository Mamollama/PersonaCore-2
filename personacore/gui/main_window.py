"""PersonaCore 2 — Main application window orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QPalette
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QLabel, QProgressBar,
    QFileDialog, QMessageBox, QApplication,
)

from personacore.gui.theme import Colors, Fonts
from personacore.gui.widgets.title_bar import TitleBar
from personacore.gui.widgets.sidebar import SidebarPanel
from personacore.gui.widgets.prompt_studio import PromptStudio
from personacore.gui.widgets.step_tracker import StepTracker
from personacore.gui.widgets.settings_panel import SettingsPanel
from personacore.gui.widgets.log_console import LogConsole
from personacore.gui.widgets.video_preview import VideoPreviewWidget
from personacore.gui.components import StatBadge
from personacore.gui.animations import fade_in

from personacore.ai.ollama_client import OllamaClient
from personacore.ai.model_manager import ModelManager
from personacore.ai.personas import PersonaManager
from personacore.ai.prompt_enricher import PromptEnricher

from personacore.video.registry import get_registry
from personacore.video.base_generator import GenerationParams

from personacore.workers.enrichment_worker import EnrichmentWorker
from personacore.workers.generation_worker import GenerationWorker
from personacore.workers.model_refresh_worker import ModelRefreshWorker

from personacore.config.settings import get_settings
from personacore.project.project_manager import ProjectManager
from personacore.export.exporter import Exporter, ExportOptions, ExportFormat
from personacore.logging_module.logger import get_app_logger, get_logger

import psutil

log = get_logger("ui.main")


class StatusBar(QWidget):
    """Custom bottom status bar with stats."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet(f"""
            background: {Colors.BG_DEEP};
            border-top: 1px solid {Colors.BORDER_SUBTLE};
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self._status = QLabel("Ready")
        self._status.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px;")
        layout.addWidget(self._status)

        layout.addStretch()

        self._gpu_badge = StatBadge("GPU", "—", Colors.CYAN)
        self._cpu_badge = StatBadge("CPU", "—", Colors.VIOLET)
        self._ram_badge = StatBadge("RAM", "—", Colors.MAGENTA)
        self._ollama_badge = StatBadge("Ollama", "—", Colors.SUCCESS)

        for badge in [self._gpu_badge, self._cpu_badge, self._ram_badge, self._ollama_badge]:
            layout.addWidget(badge)

        # Sys stats timer
        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(2000)
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start()

    def set_status(self, msg: str, color: str = Colors.TEXT_MUTED) -> None:
        self._status.setText(msg)
        self._status.setStyleSheet(f"color: {color}; font-size: 9px;")

    def set_ollama_status(self, alive: bool) -> None:
        if alive:
            self._ollama_badge.set_value("online")
            self._ollama_badge._value.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: 10px; font-weight: 700;"
            )
        else:
            self._ollama_badge.set_value("offline")
            self._ollama_badge._value.setStyleSheet(
                f"color: {Colors.ERROR}; font-size: 10px; font-weight: 700;"
            )

    def _update_stats(self) -> None:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            self._cpu_badge.set_value(f"{cpu:.0f}%")
            ram_gb = ram.used / (1024**3)
            self._ram_badge.set_value(f"{ram_gb:.1f}GB")

            try:
                import subprocess
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=1
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split(",")
                    if len(parts) >= 1:
                        self._gpu_badge.set_value(f"{parts[0].strip()}%")
                else:
                    self._gpu_badge.set_value("N/A")
            except Exception:
                self._gpu_badge.set_value("N/A")
        except Exception:
            pass


class MainWindow(QWidget):
    """
    Frameless main window — the PersonaCore 2 workstation layout.

    Layout:
        Title bar
        ┌─────────┬──────────────────────────────┬──────────────┐
        │ Sidebar │   Center (PromptStudio)       │ Settings     │
        │         │   + StepTracker               │              │
        │         │   + VideoPreview              │ + LogConsole │
        └─────────┴──────────────────────────────┴──────────────┘
        Status bar
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(1100, 700)
        self.resize(1400, 860)

        self._settings = get_settings()
        self._init_backend()
        self._build_ui()
        self._connect_signals()
        self._post_init()

    # ─────────────────────────── Backend Init ────────────────────────────────

    def _init_backend(self) -> None:
        url = self._settings.get("ollama", "base_url", default="http://localhost:11434")
        timeout = self._settings.get("ollama", "timeout", default=120)
        self._ollama = OllamaClient(base_url=url, timeout=timeout)
        self._enricher = PromptEnricher(self._ollama)

        self._model_manager = ModelManager(self._ollama)

        personas_dir = self._settings.personas_dir
        self._persona_manager = PersonaManager(personas_dir)

        projects_dir = self._settings.projects_dir
        self._project_manager = ProjectManager(projects_dir)

        self._registry = get_registry()
        self._exporter = Exporter()

        self._enrichment_worker: EnrichmentWorker | None = None
        self._generation_worker: GenerationWorker | None = None
        self._current_output: Path | None = None

        app_logger = get_app_logger()
        app_logger.log_emitted.connect(self._on_log_emitted)

    # ─────────────────────────── UI Build ────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        self._title_bar = TitleBar("PersonaCore 2", self)
        self._title_bar.close_requested.connect(self.close)
        self._title_bar.minimize_requested.connect(self.showMinimized)
        self._title_bar.maximize_requested.connect(self._toggle_maximize)
        root.addWidget(self._title_bar)

        # Main content area
        main = QWidget()
        main.setStyleSheet(f"background: {Colors.BG_BASE};")
        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Horizontal splitter ──────────────────────────────────────
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setChildrenCollapsible(False)
        h_splitter.setHandleWidth(2)

        # Left sidebar
        self._sidebar = SidebarPanel()
        h_splitter.addWidget(self._sidebar)

        # Center area (vertical splitter)
        center = QWidget()
        center.setStyleSheet(f"background: {Colors.BG_BASE};")
        center_v = QVBoxLayout(center)
        center_v.setContentsMargins(0, 0, 0, 0)
        center_v.setSpacing(0)

        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setChildrenCollapsible(False)

        self._prompt_studio = PromptStudio()
        v_splitter.addWidget(self._prompt_studio)

        # Step tracker + video preview in a panel
        bottom_center = QWidget()
        bottom_center.setStyleSheet(f"background: {Colors.BG_PANEL};")
        bottom_center_l = QVBoxLayout(bottom_center)
        bottom_center_l.setContentsMargins(12, 8, 12, 8)
        bottom_center_l.setSpacing(8)

        self._step_tracker = StepTracker()
        bottom_center_l.addWidget(self._step_tracker)

        self._video_preview = VideoPreviewWidget()
        bottom_center_l.addWidget(self._video_preview, stretch=1)

        v_splitter.addWidget(bottom_center)
        v_splitter.setSizes([400, 380])
        center_v.addWidget(v_splitter)

        h_splitter.addWidget(center)

        # Right panel (settings + log console in vertical layout)
        right = QWidget()
        right.setStyleSheet(f"background: {Colors.BG_PANEL};")
        right_v = QVBoxLayout(right)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(0)

        self._settings_panel = SettingsPanel()
        right_v.addWidget(self._settings_panel, stretch=1)

        self._log_console = LogConsole()
        right_v.addWidget(self._log_console)

        h_splitter.addWidget(right)
        h_splitter.setSizes([230, 780, 270])

        main_layout.addWidget(h_splitter)
        root.addWidget(main, stretch=1)

        # Status bar
        self._status_bar = StatusBar()
        root.addWidget(self._status_bar)

    # ─────────────────────────── Signal Wiring ───────────────────────────────

    def _connect_signals(self) -> None:
        # Sidebar signals
        self._sidebar.new_project_requested.connect(self._on_new_project)
        self._sidebar.project_selected.connect(self._on_open_project)
        self._sidebar.model_changed.connect(self._on_model_changed)
        self._sidebar.persona_changed.connect(self._on_persona_changed)
        self._sidebar.refresh_models_requested.connect(self._refresh_models)
        self._sidebar.history_item_selected.connect(self._on_history_selected)

        # Prompt studio signals
        self._prompt_studio.enrich_requested.connect(self._on_enrich_requested)
        self._prompt_studio.generate_requested.connect(self._on_generate_requested)
        self._prompt_studio.cancel_requested.connect(self._on_cancel_requested)

        # Settings signals
        self._settings_panel.export_requested.connect(self._on_export_requested)
        self._settings_panel.backend_changed.connect(self._on_backend_changed)

    # ─────────────────────────── Post-Init ───────────────────────────────────

    def _post_init(self) -> None:
        # Load UI state
        self._sidebar.set_personas(self._persona_manager.all())
        self._sidebar.set_projects(self._project_manager.list_projects())

        # Load available backends
        backends = self._registry.available_backends()
        self._settings_panel.set_backends(backends)

        # Refresh models
        QTimer.singleShot(300, self._refresh_models)

        # Fade in
        fade_in(self, 350)

        log.info("PersonaCore 2 initialized")
        self._status_bar.set_status("Ready — enrich a prompt to get started", Colors.TEXT_MUTED)

        # Restore last project
        last = self._settings.get("project", "last_project", default="")
        if last:
            self._project_manager.open_project(last)

    # ─────────────────────────── Model Refresh ───────────────────────────────

    def _refresh_models(self) -> None:
        self._status_bar.set_status("Connecting to Ollama…", Colors.CYAN)
        worker = ModelRefreshWorker(self._ollama)
        worker.models_loaded.connect(self._on_models_loaded)
        worker.error_occurred.connect(self._on_models_error)
        worker.ollama_status.connect(self._on_ollama_status)
        worker.finished.connect(worker.deleteLater)
        self._refresh_worker = worker
        worker.start()

    def _on_models_loaded(self, models: list) -> None:
        self._sidebar.set_models(models)
        self._status_bar.set_status(f"Loaded {len(models)} models", Colors.SUCCESS)
        log.info("Models loaded: %d available", len(models))

    def _on_models_error(self, error: str) -> None:
        self._status_bar.set_status(f"Ollama: {error}", Colors.ERROR)
        log.warning("Model refresh error: %s", error)

    def _on_ollama_status(self, alive: bool) -> None:
        self._sidebar.set_ollama_status(alive)
        self._status_bar.set_ollama_status(alive)

    # ─────────────────────────── Model/Persona ───────────────────────────────

    def _on_model_changed(self, model: str) -> None:
        self._model_manager.selected_model = model
        self._settings.set("ollama", "default_model", model)
        log.info("Model selected: %s", model)

    def _on_persona_changed(self, persona_id: str) -> None:
        self._settings.set("ollama", "system_prompt_preset", persona_id)
        log.info("Persona selected: %s", persona_id)

    # ─────────────────────────── Enrichment ──────────────────────────────────

    def _on_enrich_requested(self, raw_prompt: str) -> None:
        model = self._sidebar.current_model()
        if not model:
            self._show_error("No model selected", "Select an Ollama model from the sidebar.")
            return

        persona_id = self._sidebar.current_persona_id()
        persona = self._persona_manager.get(persona_id) or self._persona_manager.all()[0]

        self._step_tracker.set_step("enrich")
        self._status_bar.set_status("Enriching prompt…", Colors.VIOLET)

        if self._enrichment_worker and self._enrichment_worker.isRunning():
            self._enrichment_worker.cancel()
            self._enrichment_worker.wait(1000)

        worker = EnrichmentWorker(self._ollama, raw_prompt, model, persona)
        worker.chunk_received.connect(self._prompt_studio.append_enriched_chunk)
        worker.finished.connect(self._on_enrichment_done)
        worker.error_occurred.connect(self._on_enrichment_error)
        worker.finished.connect(worker.deleteLater)
        self._enrichment_worker = worker
        worker.start()

    def _on_enrichment_done(self, full_text: str) -> None:
        self._prompt_studio.on_enrichment_done(full_text)
        self._step_tracker.set_step("generating")  # Prime next step
        self._step_tracker.reset()
        self._status_bar.set_status("Enrichment complete — review and generate", Colors.SUCCESS)

        # Save to project and history
        raw = self._prompt_studio.get_raw_prompt()
        project = self._project_manager.current
        if project:
            project.raw_prompt = raw
            project.enriched_prompt = full_text
            self._project_manager.save_current()

        self._sidebar.add_history_entry(raw, {"raw": raw, "enriched": full_text})
        log.info("Enrichment complete (%d chars)", len(full_text))

    def _on_enrichment_error(self, error: str) -> None:
        self._prompt_studio.on_enrichment_error(error)
        self._step_tracker.set_error("enrich")
        self._status_bar.set_status(f"Enrichment failed: {error}", Colors.ERROR)
        log.error("Enrichment error: %s", error)

    # ─────────────────────────── Generation ──────────────────────────────────

    def _on_generate_requested(self, enriched_prompt: str, _technical: str) -> None:
        backend_id = self._settings_panel.get_selected_backend()
        generator = self._registry.create(backend_id)
        if not generator:
            self._show_error("Backend unavailable", f"Cannot create generator: {backend_id}")
            return

        if not generator.is_available():
            self._show_error(
                "Backend not available",
                f"{generator.name} requires dependencies that are not installed.\n"
                "Try the Demo backend, or install the optional diffusers extras."
            )
            return

        params = self._settings_panel.build_generation_params(enriched_prompt)

        project = self._project_manager.current
        if not project:
            project = self._project_manager.new_project("Untitled")

        output_dir = self._project_manager.get_output_dir(project)
        output_dir = output_dir / f"run_{len(list(output_dir.iterdir()))}"

        self._step_tracker.set_step("generating")
        self._status_bar.set_status(f"Generating with {generator.name}…", Colors.CYAN)

        if self._generation_worker and self._generation_worker.isRunning():
            self._generation_worker.cancel()
            self._generation_worker.wait(2000)

        worker = GenerationWorker(generator, params, output_dir)
        worker.progress.connect(self._on_generation_progress)
        worker.step_changed.connect(self._on_generation_step)
        worker.finished.connect(self._on_generation_done)
        worker.error_occurred.connect(self._on_generation_error)
        worker.finished.connect(worker.deleteLater)
        self._generation_worker = worker
        worker.start()

    def _on_generation_progress(self, fraction: float, message: str) -> None:
        self._status_bar.set_status(message, Colors.CYAN)

    def _on_generation_step(self, step: str) -> None:
        if step not in ("complete", "error", "cancelled"):
            self._step_tracker.set_step(step)
        elif step == "complete":
            self._step_tracker.set_complete()
        elif step == "error":
            self._step_tracker.set_error()
        elif step == "cancelled":
            self._step_tracker.set_step("cancelled")

    def _on_generation_done(self, result) -> None:
        self._prompt_studio.on_generation_done()
        if result.success and result.output_path:
            self._current_output = result.output_path
            self._video_preview.load_video(result.output_path)

            project = self._project_manager.current
            if project:
                project.output_paths.append(str(result.output_path))
                project.add_history_entry("generation", {
                    "output": str(result.output_path),
                    "duration": result.duration_seconds,
                })
                self._project_manager.save_current()

            self._status_bar.set_status(
                f"Generation complete → {result.output_path.name}", Colors.SUCCESS
            )
            log.info("Generation complete: %s", result.output_path)
        else:
            self._status_bar.set_status("Generation failed", Colors.ERROR)

    def _on_generation_error(self, error: str) -> None:
        self._prompt_studio.on_generation_error(error)
        self._status_bar.set_status(f"Generation error: {error}", Colors.ERROR)
        log.error("Generation error: %s", error)

    # ─────────────────────────── Cancel ──────────────────────────────────────

    def _on_cancel_requested(self) -> None:
        cancelled = False
        if self._enrichment_worker and self._enrichment_worker.isRunning():
            self._enrichment_worker.cancel()
            cancelled = True
        if self._generation_worker and self._generation_worker.isRunning():
            self._generation_worker.cancel()
            cancelled = True

        if cancelled:
            self._prompt_studio.on_cancel()
            self._step_tracker.set_step("cancelled")
            self._status_bar.set_status("Cancelled", Colors.WARNING)
            log.info("Operation cancelled by user")

    # ─────────────────────────── Project ─────────────────────────────────────

    def _on_new_project(self) -> None:
        project = self._project_manager.new_project("New Project")
        self._sidebar.set_projects(self._project_manager.list_projects())
        self._prompt_studio.set_raw_prompt("")
        self._prompt_studio.set_enriched_prompt("")
        self._step_tracker.reset()
        self._settings.set("project", "last_project", project.id)
        self._settings.save()
        log.info("New project: %s", project.name)

    def _on_open_project(self, project_id: str) -> None:
        project = self._project_manager.open_project(project_id)
        if project:
            if project.raw_prompt:
                self._prompt_studio.set_raw_prompt(project.raw_prompt)
            if project.enriched_prompt:
                self._prompt_studio.set_enriched_prompt(project.enriched_prompt)
            if project.latest_output:
                self._video_preview.load_video(project.latest_output)
            self._settings.set("project", "last_project", project.id)
            self._settings.save()
            self._status_bar.set_status(f"Opened: {project.name}", Colors.SUCCESS)

    def _on_history_selected(self, data: dict) -> None:
        if "raw" in data:
            self._prompt_studio.set_raw_prompt(data["raw"])
        if "enriched" in data:
            self._prompt_studio.set_enriched_prompt(data["enriched"])

    # ─────────────────────────── Export ──────────────────────────────────────

    def _on_export_requested(self, fmt: str) -> None:
        if not self._current_output or not self._current_output.exists():
            self._show_error("No output", "Generate a video first.")
            return

        fmt_enum = {"mp4": ExportFormat.MP4, "gif": ExportFormat.GIF, "webm": ExportFormat.WEBM}.get(fmt, ExportFormat.MP4)
        ext = {"mp4": "mp4", "gif": "gif", "webm": "webm"}.get(fmt, "mp4")
        filter_ = {"mp4": "MP4 Video (*.mp4)", "gif": "GIF Image (*.gif)", "webm": "WebM Video (*.webm)"}.get(fmt, "")

        dest, _ = QFileDialog.getSaveFileName(
            self, "Export Video", str(Path.home() / f"personacore_export.{ext}"), filter_
        )
        if not dest:
            return

        opts = ExportOptions(format=fmt_enum)
        ok = self._exporter.export(self._current_output, Path(dest), opts)
        if ok:
            self._status_bar.set_status(f"Exported: {Path(dest).name}", Colors.SUCCESS)
            log.info("Exported to: %s", dest)
        else:
            self._show_error("Export failed", "Check that FFmpeg is installed.")

    def _on_backend_changed(self, backend_id: str) -> None:
        log.info("Video backend changed to: %s", backend_id)
        self._settings.set("video", "backend", backend_id)

    # ─────────────────────────── Logging ─────────────────────────────────────

    def _on_log_emitted(self, level: int, name: str, message: str) -> None:
        self._log_console.append_log(level, name, message)

    # ─────────────────────────── Window ──────────────────────────────────────

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _show_error(self, title: str, message: str) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.TEXT_PRIMARY};
            }}
            QLabel {{ color: {Colors.TEXT_PRIMARY}; }}
            QPushButton {{
                background: {Colors.VIOLET};
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                color: white;
                min-width: 80px;
            }}
        """)
        msg.exec()

    def closeEvent(self, event) -> None:
        log.info("Shutting down PersonaCore 2")
        if self._enrichment_worker and self._enrichment_worker.isRunning():
            self._enrichment_worker.cancel()
            self._enrichment_worker.wait(1000)
        if self._generation_worker and self._generation_worker.isRunning():
            self._generation_worker.cancel()
            self._generation_worker.wait(2000)
        self._settings.save()
        self._ollama.close()
        event.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel_requested()
        super().keyPressEvent(event)
