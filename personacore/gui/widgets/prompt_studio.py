"""Prompt Studio — raw input + enriched output panels with streaming display."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from personacore.gui.components import GlowButton
from personacore.gui.theme import Colors


class _PanelHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        accent: str = Colors.VIOLET,
        parent=None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        bar = QWidget()
        bar.setFixedSize(3, 18)
        bar.setStyleSheet(f"background: {accent}; border-radius: 1px;")
        layout.addWidget(bar)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 12px;
            font-weight: 700;
        """)
        layout.addWidget(title_lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px;")
            layout.addWidget(sub)

        layout.addStretch()


class PromptStudio(QWidget):
    """Center stage — raw prompt input, AI enrichment output, action buttons."""

    enrich_requested = pyqtSignal(str)      # raw prompt text
    generate_requested = pyqtSignal(str, str)  # enriched prompt, technical prompt
    cancel_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_enriching = False
        self._is_generating = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Prompt Studio")
        title.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.5px;
        """)
        header.addWidget(title)

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px;")
        header.addWidget(self._status_dot)
        header.addStretch()

        self._cancel_btn = QPushButton("✕ Cancel")
        self._cancel_btn.setFixedSize(80, 28)
        self._cancel_btn.setProperty("accent", "danger")
        self._cancel_btn.clicked.connect(self.cancel_requested)
        self._cancel_btn.hide()
        header.addWidget(self._cancel_btn)

        layout.addLayout(header)

        # ── Splitter — Raw / Enriched ────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # Raw prompt panel
        raw_panel = QWidget()
        raw_layout = QVBoxLayout(raw_panel)
        raw_layout.setContentsMargins(0, 0, 0, 0)
        raw_layout.setSpacing(6)
        raw_layout.addWidget(
            _PanelHeader("Your Concept", "Describe your video idea", Colors.VIOLET)
        )

        self._raw_input = QTextEdit()
        self._raw_input.setPlaceholderText(
            "Describe your video concept in natural language…\n\n"
            'e.g. "A lone astronaut walks across the red surface of Mars at sunset, '
            'their visor reflecting swirling dust storms, epic cinematic score"'
        )
        self._raw_input.setFont(QFont("Inter", 12))
        self._raw_input.setMinimumHeight(120)
        self._raw_input.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 10px;
                padding: 14px;
                font-size: 12px;
                line-height: 1.6;
                color: {Colors.TEXT_PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {Colors.VIOLET};
                background: {Colors.BG_ELEVATED};
            }}
        """)
        raw_layout.addWidget(self._raw_input)

        # Enrich button
        btn_row = QHBoxLayout()
        self._enrich_btn = GlowButton("✦ Enrich with AI", Colors.VIOLET, filled=True)
        self._enrich_btn.setFixedHeight(40)
        self._enrich_btn.clicked.connect(self._on_enrich_clicked)
        btn_row.addWidget(self._enrich_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedSize(60, 40)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 6px;
                color: {Colors.TEXT_MUTED};
                font-size: 10px;
            }}
            QPushButton:hover {{ border-color: {Colors.MAGENTA}; color: {Colors.MAGENTA}; }}
        """)
        self._clear_btn.clicked.connect(self._raw_input.clear)
        btn_row.addWidget(self._clear_btn)
        raw_layout.addLayout(btn_row)

        splitter.addWidget(raw_panel)

        # Enriched prompt panel
        enriched_panel = QWidget()
        enriched_layout = QVBoxLayout(enriched_panel)
        enriched_layout.setContentsMargins(0, 0, 0, 0)
        enriched_layout.setSpacing(6)

        enriched_header = QHBoxLayout()
        enriched_header.addWidget(
            _PanelHeader("Director's Vision", "AI-enriched prompt (editable)", Colors.CYAN)
        )
        self._copy_enriched_btn = QPushButton("Copy")
        self._copy_enriched_btn.setFixedSize(50, 22)
        self._copy_enriched_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 4px;
                color: {Colors.TEXT_MUTED};
                font-size: 9px;
            }}
            QPushButton:hover {{ border-color: {Colors.CYAN}; color: {Colors.CYAN}; }}
        """)
        self._copy_enriched_btn.clicked.connect(self._copy_enriched)
        enriched_header.addWidget(self._copy_enriched_btn)
        enriched_layout.addLayout(enriched_header)

        self._enriched_output = QTextEdit()
        self._enriched_output.setPlaceholderText(
            "The AI director's expanded prompt will stream here…\n"
            "You can edit it before generating."
        )
        self._enriched_output.setFont(QFont("JetBrains Mono", 10))
        self._enriched_output.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 10px;
                padding: 14px;
                font-size: 10px;
                line-height: 1.5;
                color: {Colors.CYAN};
            }}
            QTextEdit:focus {{
                border-color: {Colors.CYAN};
                background: {Colors.BG_ELEVATED};
            }}
        """)
        enriched_layout.addWidget(self._enriched_output)

        # Generate button
        self._generate_btn = GlowButton("▶ Generate Video", Colors.CYAN, filled=False)
        self._generate_btn.setFixedHeight(44)
        self._generate_btn.setEnabled(False)
        self._generate_btn.clicked.connect(self._on_generate_clicked)
        enriched_layout.addWidget(self._generate_btn)

        splitter.addWidget(enriched_panel)
        splitter.setSizes([250, 350])

        layout.addWidget(splitter)

    def _on_enrich_clicked(self) -> None:
        text = self._raw_input.toPlainText().strip()
        if not text:
            return
        self._enriched_output.clear()
        self._set_enriching(True)
        self.enrich_requested.emit(text)

    def _on_generate_clicked(self) -> None:
        enriched = self._enriched_output.toPlainText().strip()
        if not enriched:
            return
        self._set_generating(True)
        self.generate_requested.emit(enriched, enriched)

    def _set_enriching(self, active: bool) -> None:
        self._is_enriching = active
        self._enrich_btn.setEnabled(not active)
        self._cancel_btn.setVisible(active)
        if active:
            self._status_dot.setStyleSheet(f"color: {Colors.VIOLET}; font-size: 14px;")
            self._enrich_btn.start_pulse()
        else:
            self._status_dot.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px;")
            self._enrich_btn.stop_pulse()

    def _set_generating(self, active: bool) -> None:
        self._is_generating = active
        self._generate_btn.setEnabled(not active)
        self._cancel_btn.setVisible(active)
        if active:
            self._status_dot.setStyleSheet(f"color: {Colors.CYAN}; font-size: 14px;")
            self._generate_btn.start_pulse()
        else:
            self._status_dot.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px;")
            self._generate_btn.stop_pulse()

    # ── Public API ───────────────────────────────────────────────────────

    def append_enriched_chunk(self, chunk: str) -> None:
        self._enriched_output.moveCursor(QTextCursor.MoveOperation.End)
        self._enriched_output.insertPlainText(chunk)
        self._enriched_output.ensureCursorVisible()

    def on_enrichment_done(self, full_text: str) -> None:
        self._set_enriching(False)
        self._generate_btn.setEnabled(True)

    def on_enrichment_error(self, error: str) -> None:
        self._set_enriching(False)
        self._enriched_output.setPlainText(f"[Error: {error}]")

    def on_generation_done(self) -> None:
        self._set_generating(False)

    def on_generation_error(self, error: str) -> None:
        self._set_generating(False)

    def on_cancel(self) -> None:
        self._set_enriching(False)
        self._set_generating(False)

    def get_raw_prompt(self) -> str:
        return self._raw_input.toPlainText().strip()

    def get_enriched_prompt(self) -> str:
        return self._enriched_output.toPlainText().strip()

    def set_raw_prompt(self, text: str) -> None:
        self._raw_input.setPlainText(text)

    def set_enriched_prompt(self, text: str) -> None:
        self._enriched_output.setPlainText(text)

    def _copy_enriched(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._enriched_output.toPlainText())
