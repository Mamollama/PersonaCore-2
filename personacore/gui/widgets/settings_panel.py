"""Right panel — generation settings, style presets, export controls."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QGroupBox, QFormLayout, QCheckBox, QScrollArea,
    QSizePolicy, QTabWidget,
)

from PyQt6.QtGui import QStandardItemModel
from personacore.gui.theme import Colors
from personacore.video.base_generator import GenerationParams

STYLE_PRESETS = {
    "cinematic":   {"guidance_scale": 8.5, "num_inference_steps": 30, "fps": 8},
    "anime":       {"guidance_scale": 7.0, "num_inference_steps": 25, "fps": 12},
    "documentary": {"guidance_scale": 6.5, "num_inference_steps": 20, "fps": 8},
    "neon_noir":   {"guidance_scale": 9.0, "num_inference_steps": 35, "fps": 8},
    "abstract":    {"guidance_scale": 10.0, "num_inference_steps": 40, "fps": 12},
}

RESOLUTIONS = {
    "256×256":   (256, 256),
    "512×512":   (512, 512),
    "576×320":   (576, 320),
    "768×432":   (768, 432),
    "1024×576":  (1024, 576),
}


class SettingsPanel(QWidget):
    """Right-side panel for video generation parameters."""

    settings_changed = pyqtSignal(dict)
    export_requested = pyqtSignal(str)   # format name
    backend_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)
        self.setObjectName("SettingsPanel")
        self.setStyleSheet(f"""
            QWidget#SettingsPanel {{
                background: {Colors.BG_PANEL};
                border-left: 1px solid {Colors.BORDER_SUBTLE};
            }}
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 6px;
                background: {Colors.BG_SURFACE};
            }}
        """)

        # ── Generation Tab ─────────────────────────────────────────────
        gen_tab = QWidget()
        gen_tab.setStyleSheet("background: transparent;")
        gen_layout = QVBoxLayout(gen_tab)
        gen_layout.setContentsMargins(8, 8, 8, 8)
        gen_layout.setSpacing(10)

        # Style preset
        self._add_section(gen_layout, "STYLE PRESET")
        self._preset_combo = QComboBox()
        for p in STYLE_PRESETS:
            self._preset_combo.addItem(p.title(), p)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        gen_layout.addWidget(self._preset_combo)

        # Backend
        self._add_section(gen_layout, "VIDEO BACKEND")
        model = QStandardItemModel(self._backend_combo)
        self._backend_combo.setModel(model)
        self._backend_combo.addItem("Demo (No Model)", "demo")
        self._backend_combo.addItem("Zeroscope v2", "zeroscope")
        self._backend_combo.addItem("AnimateDiff", "animatediff")
        self._backend_combo.currentIndexChanged.connect(
            lambda: self.backend_changed.emit(self._backend_combo.currentData() or "demo")
        )
        gen_layout.addWidget(self._backend_combo)

        # Resolution
        self._add_section(gen_layout, "RESOLUTION")
        self._res_combo = QComboBox()
        for label in RESOLUTIONS:
            self._res_combo.addItem(label, RESOLUTIONS[label])
        self._res_combo.setCurrentIndex(1)
        gen_layout.addWidget(self._res_combo)

        # FPS
        self._add_section(gen_layout, "FRAME RATE (FPS)")
        self._fps_spin = self._make_spin(1, 60, 8, "fps")
        gen_layout.addWidget(self._fps_spin)

        # Duration
        self._add_section(gen_layout, "DURATION (SECONDS)")
        self._duration_spin = self._make_dspin(1.0, 30.0, 3.0, 0.5, "s")
        gen_layout.addWidget(self._duration_spin)

        # Guidance
        self._add_section(gen_layout, "GUIDANCE SCALE")
        self._guidance_row = self._make_slider_row(1.0, 20.0, 7.5)
        gen_layout.addWidget(self._guidance_row["widget"])

        # Steps
        self._add_section(gen_layout, "INFERENCE STEPS")
        self._steps_row = self._make_slider_row(5, 100, 25, is_int=True)
        gen_layout.addWidget(self._steps_row["widget"])

        # Seed
        self._add_section(gen_layout, "SEED (-1 = RANDOM)")
        self._seed_spin = self._make_spin(-1, 2**31, -1, "")
        gen_layout.addWidget(self._seed_spin)

        # GPU
        self._gpu_check = QCheckBox("Use GPU acceleration")
        self._gpu_check.setChecked(True)
        self._gpu_check.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 10px;")
        gen_layout.addWidget(self._gpu_check)

        # GPU budget
        self._add_section(gen_layout, "GPU MEMORY BUDGET (GB)")
        self._gpu_budget = self._make_slider_row(1.0, 24.0, 6.0, is_int=False)
        gen_layout.addWidget(self._gpu_budget["widget"])

        gen_layout.addStretch()
        tabs.addTab(gen_tab, "Generate")

        # ── Export Tab ─────────────────────────────────────────────────
        exp_tab = QWidget()
        exp_tab.setStyleSheet("background: transparent;")
        exp_layout = QVBoxLayout(exp_tab)
        exp_layout.setContentsMargins(8, 8, 8, 8)
        exp_layout.setSpacing(10)

        self._add_section(exp_layout, "FORMAT")
        self._format_combo = QComboBox()
        self._format_combo.addItems(["MP4 (H.264)", "GIF", "WebM (VP9)"])
        exp_layout.addWidget(self._format_combo)

        self._add_section(exp_layout, "QUALITY (CRF)")
        self._crf_row = self._make_slider_row(0, 51, 23, is_int=True)
        exp_layout.addWidget(self._crf_row["widget"])

        export_btn = QPushButton("Export Video…")
        export_btn.setFixedHeight(36)
        export_btn.setProperty("accent", "violet")
        export_btn.clicked.connect(
            lambda: self.export_requested.emit(
                ["mp4", "gif", "webm"][self._format_combo.currentIndex()]
            )
        )
        exp_layout.addWidget(export_btn)

        exp_layout.addStretch()
        tabs.addTab(exp_tab, "Export")

        layout.addWidget(tabs)
        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _add_section(self, layout, text: str) -> None:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 8px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-top: 4px;
        """)
        layout.addWidget(lbl)

    def _make_spin(self, mn: int, mx: int, val: int, suffix: str) -> QSpinBox:
        s = QSpinBox()
        s.setRange(mn, mx)
        s.setValue(val)
        s.setSuffix(f" {suffix}" if suffix else "")
        s.valueChanged.connect(self._emit_settings)
        return s

    def _make_dspin(self, mn: float, mx: float, val: float, step: float, suffix: str) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(mn, min(mx, 2**31 - 1))
        s.setValue(val)
        s.setSingleStep(step)
        s.setSuffix(f" {suffix}")
        s.valueChanged.connect(self._emit_settings)
        return s

    def _make_slider_row(self, mn, mx, val, is_int: bool = False) -> dict:
        row_w = QWidget()
        row_w.setStyleSheet("background: transparent;")
        row_l = QHBoxLayout(row_w)
        row_l.setContentsMargins(0, 0, 0, 0)
        row_l.setSpacing(8)

        scale = 100 if not is_int else 1
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(int(mn * scale), int(mx * scale))
        slider.setValue(int(val * scale))

        val_lbl = QLabel(f"{val:.1f}" if not is_int else str(int(val)))
        val_lbl.setFixedWidth(36)
        val_lbl.setStyleSheet(f"color: {Colors.CYAN}; font-size: 9px; font-family: 'JetBrains Mono';")

        def _update(v):
            real = v / scale
            val_lbl.setText(f"{real:.1f}" if not is_int else str(int(real)))
            self._emit_settings()

        slider.valueChanged.connect(_update)
        row_l.addWidget(slider, stretch=1)
        row_l.addWidget(val_lbl)

        return {"widget": row_w, "slider": slider, "label": val_lbl, "scale": scale, "is_int": is_int}

    def _on_preset_changed(self) -> None:
        preset_id = self._preset_combo.currentData()
        if preset_id and preset_id in STYLE_PRESETS:
            p = STYLE_PRESETS[preset_id]
            scale = self._guidance_row["scale"]
            self._guidance_row["slider"].setValue(int(p["guidance_scale"] * scale))
            scale2 = self._steps_row["scale"]
            self._steps_row["slider"].setValue(int(p["num_inference_steps"] * scale2))
            self._fps_spin.setValue(p["fps"])
        self._emit_settings()

    def _emit_settings(self) -> None:
        self.settings_changed.emit(self.get_params_dict())

    def get_params_dict(self) -> dict:
        res = self._res_combo.currentData() or (512, 512)
        g_scale = self._guidance_row["slider"].value() / self._guidance_row["scale"]
        steps = self._steps_row["slider"].value() // self._steps_row["scale"] if self._steps_row["is_int"] else \
                self._steps_row["slider"].value() / self._steps_row["scale"]
        gpu_budget = self._gpu_budget["slider"].value() / self._gpu_budget["scale"]

        return {
            "resolution": res,
            "fps": self._fps_spin.value(),
            "duration_seconds": self._duration_spin.value(),
            "guidance_scale": g_scale,
            "num_inference_steps": int(steps),
            "seed": self._seed_spin.value(),
            "use_gpu": self._gpu_check.isChecked(),
            "gpu_memory_budget_gb": gpu_budget,
            "style_preset": self._preset_combo.currentData() or "cinematic",
            "backend": self._backend_combo.currentData() or "demo",
        }

    def build_generation_params(self, prompt: str, negative_prompt: str = "") -> GenerationParams:
        d = self.get_params_dict()
        return GenerationParams(
            prompt=prompt,
            negative_prompt=negative_prompt,
            resolution=(d["resolution"], d["resolution"]),  # Ensure resolution is passed as a tuple
            fps=d["fps"],
            duration_seconds=d["duration_seconds"],
            guidance_scale=d["guidance_scale"],
            num_inference_steps=d["num_inference_steps"],
            seed=d["seed"],
            use_gpu=d["use_gpu"],
            gpu_memory_budget_gb=d["gpu_memory_budget_gb"],
            style_preset=d["style_preset"],
        )

    def set_backends(self, backends: list[tuple[str, str, bool]]) -> None:
        self._backend_combo.blockSignals(True)
        self._backend_combo.clear()
        for bid, name, available in backends:
            label = f"{'✓' if available else '✗'} {name}"
            self._backend_combo.addItem(label, bid)
            if not available:
                idx = self._backend_combo.count() - 1
                item = self._backend_combo.model().itemFromIndex(self._backend_combo.model().index(idx, 0))
                if item:
                    item.setEnabled(available)
        self._backend_combo.blockSignals(False)

    def get_selected_backend(self) -> str:
        return self._backend_combo.currentData() or "demo"
