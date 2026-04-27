"""Small stat badge widget for status bar and panels."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QBrush
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel

from personacore.gui.theme import Colors


class StatBadge(QWidget):
    """Compact badge showing a label + value pair with accent color."""

    def __init__(
        self,
        label: str,
        value: str = "—",
        accent: str = Colors.CYAN,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._accent = accent
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(5)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-weight: 600;")
        self._value = QLabel(value)
        self._value.setStyleSheet(f"color: {accent}; font-size: 10px; font-weight: 700; font-family: 'JetBrains Mono';")

        layout.addWidget(self._label)
        layout.addWidget(self._value)
        self.setFixedHeight(22)

    def set_value(self, v: str) -> None:
        self._value.setText(v)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        r = self.rect()
        path.addRoundedRect(0, 0, r.width(), r.height(), 4, 4)
        bg = QColor(self._accent)
        bg.setAlpha(20)
        painter.fillPath(path, QBrush(bg))
        painter.end()
        super().paintEvent(event)
