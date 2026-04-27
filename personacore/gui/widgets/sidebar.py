"""Left sidebar — project navigator, model selector, history, personas."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QFrame, QSizePolicy,
    QScrollArea,
)

from personacore.gui.theme import Colors
from personacore.gui.components import GlowButton


class _SectionHeader(QWidget):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)
        label = QLabel(text.upper())
        label.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        layout.addWidget(label)
        layout.addStretch()


class _Divider(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {Colors.BORDER_SUBTLE};")


class SidebarPanel(QWidget):
    """Left panel — project nav, model selector, history."""

    project_selected = pyqtSignal(str)
    new_project_requested = pyqtSignal()
    model_changed = pyqtSignal(str)
    persona_changed = pyqtSignal(str)
    history_item_selected = pyqtSignal(dict)
    refresh_models_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
        self.setObjectName("SidebarPanel")
        self.setStyleSheet(f"""
            QWidget#SidebarPanel {{
                background: {Colors.BG_PANEL};
                border-right: 1px solid {Colors.BORDER_SUBTLE};
            }}
        """)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        # ── Projects ──────────────────────────────────────────────────
        layout.addWidget(_SectionHeader("Projects"))
        self._new_btn = GlowButton("+ New Project", Colors.VIOLET)
        self._new_btn.setFixedHeight(32)
        self._new_btn.clicked.connect(self.new_project_requested)
        layout.addWidget(self._new_btn)

        self._project_list = QListWidget()
        self._project_list.setMaximumHeight(160)
        self._project_list.setStyleSheet(f"""
            QListWidget {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 6px;
                font-size: 10px;
            }}
            QListWidget::item {{ padding: 5px 8px; border-radius: 3px; }}
            QListWidget::item:selected {{ background: {Colors.VIOLET}; color: white; }}
        """)
        self._project_list.itemClicked.connect(
            lambda item: self.project_selected.emit(item.data(Qt.ItemDataRole.UserRole) or "")
        )
        layout.addWidget(self._project_list)

        layout.addWidget(_Divider())

        # ── AI Model ──────────────────────────────────────────────────
        layout.addWidget(_SectionHeader("Ollama Model"))
        self._model_combo = QComboBox()
        self._model_combo.addItem("⟳ Refreshing...")
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self._model_combo)

        refresh_btn = QPushButton("↻ Refresh Models")
        refresh_btn.setFixedHeight(28)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 4px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 10px;
            }}
            QPushButton:hover {{ border-color: {Colors.CYAN}; color: {Colors.CYAN}; }}
        """)
        refresh_btn.clicked.connect(self.refresh_models_requested)
        layout.addWidget(refresh_btn)

        layout.addWidget(_Divider())

        # ── Persona ──────────────────────────────────────────────────
        layout.addWidget(_SectionHeader("Director Persona"))
        self._persona_combo = QComboBox()
        self._persona_combo.currentTextChanged.connect(
            lambda t: self.persona_changed.emit(
                self._persona_combo.currentData() or t
            )
        )
        layout.addWidget(self._persona_combo)

        layout.addWidget(_Divider())

        # ── Prompt History ────────────────────────────────────────────
        layout.addWidget(_SectionHeader("Recent Prompts"))
        self._history_list = QListWidget()
        self._history_list.setMaximumHeight(180)
        self._history_list.setStyleSheet(f"""
            QListWidget {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 6px;
                font-size: 10px;
            }}
            QListWidget::item {{ padding: 5px 6px; border-radius: 3px; }}
            QListWidget::item:selected {{ background: {Colors.VIOLET}44; }}
        """)
        self._history_list.itemDoubleClicked.connect(
            lambda item: self.history_item_selected.emit(
                item.data(Qt.ItemDataRole.UserRole) or {}
            )
        )
        layout.addWidget(self._history_list)

        layout.addStretch()

        # ── Status indicator ─────────────────────────────────────────
        self._ollama_status = QLabel("● Ollama: checking...")
        self._ollama_status.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px;")
        layout.addWidget(self._ollama_status)

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_ollama_status(self, alive: bool) -> None:
        if alive:
            self._ollama_status.setText("● Ollama: connected")
            self._ollama_status.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 9px;")
        else:
            self._ollama_status.setText("● Ollama: offline")
            self._ollama_status.setStyleSheet(f"color: {Colors.ERROR}; font-size: 9px;")

    def set_models(self, models: list[dict]) -> None:
        self._model_combo.blockSignals(True)
        prev = self._model_combo.currentText()
        self._model_combo.clear()
        for m in models:
            name = m.get("name", "")
            size = m.get("size", 0)
            size_gb = f"{size / (1024**3):.1f}GB" if size else ""
            display = f"{name}  {size_gb}".strip()
            self._model_combo.addItem(display, name)
        # Restore selection
        for i in range(self._model_combo.count()):
            if self._model_combo.itemData(i) == prev:
                self._model_combo.setCurrentIndex(i)
                break
        self._model_combo.blockSignals(False)
        if models:
            self.model_changed.emit(self._model_combo.currentData() or "")

    def set_personas(self, personas: list) -> None:
        self._persona_combo.blockSignals(True)
        self._persona_combo.clear()
        for p in personas:
            self._persona_combo.addItem(p.name, p.id)
        self._persona_combo.blockSignals(False)

    def set_projects(self, projects: list) -> None:
        self._project_list.clear()
        for p in projects:
            item = QListWidgetItem(p.name)
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            item.setToolTip(f"Updated: {p.updated_at[:10]}")
            self._project_list.addItem(item)

    def add_history_entry(self, prompt: str, data: dict) -> None:
        short = prompt[:40] + "…" if len(prompt) > 40 else prompt
        item = QListWidgetItem(short)
        item.setData(Qt.ItemDataRole.UserRole, data)
        item.setToolTip(prompt)
        self._history_list.insertItem(0, item)
        while self._history_list.count() > 30:
            self._history_list.takeItem(self._history_list.count() - 1)

    def current_model(self) -> str:
        return self._model_combo.currentData() or self._model_combo.currentText()

    def current_persona_id(self) -> str:
        return self._persona_combo.currentData() or ""

    def _on_model_changed(self, text: str) -> None:
        name = self._model_combo.currentData() or text
        self.model_changed.emit(name)
