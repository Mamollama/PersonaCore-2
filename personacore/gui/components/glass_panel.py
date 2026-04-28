"""Frosted-glass-style panel with subtle border and background."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from personacore.gui.theme import Colors


class GlassPanel(QWidget):
    """A panel with frosted-glass aesthetics — translucent background, rounded corners."""

    def __init__(
        self,
        parent: QWidget | None = None,
        radius: int = 12,
        accent: str = Colors.BORDER_DEFAULT,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._radius = radius
        self._accent = accent
        self._glow = 0.0

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(1, 1, 1, 1)

    def set_glow(self, intensity: float) -> None:
        """0.0 – 1.0; drives border glow brightness."""
        self._glow = max(0.0, min(1.0, intensity))
        self.update()

    def set_accent(self, color: str) -> None:
        self._accent = color
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(),
                            self._radius, self._radius)

        # Background — deep frosted surface
        bg_grad = QLinearGradient(0, 0, 0, rect.height())
        bg_grad.setColorAt(0.0, QColor(22, 22, 32, 220))
        bg_grad.setColorAt(1.0, QColor(13, 13, 20, 240))
        painter.fillPath(path, QBrush(bg_grad))

        # Border with optional glow
        if self._glow > 0:
            accent = QColor(self._accent)
            accent.setAlphaF(0.3 + self._glow * 0.7)
            pen = QPen(accent, 1.5)
        else:
            pen = QPen(QColor(Colors.BORDER_DEFAULT), 1)

        painter.setPen(pen)
        painter.drawPath(path)
        painter.end()

    def inner_layout(self) -> QVBoxLayout:
        return self._layout
