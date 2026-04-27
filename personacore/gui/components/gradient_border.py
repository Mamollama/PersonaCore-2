"""Widget with animated rotating gradient border."""

from __future__ import annotations

import math

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QConicalGradient
from PyQt6.QtWidgets import QWidget

from personacore.gui.theme import Colors


class GradientBorderWidget(QWidget):
    """Container with an animated rainbow/accent gradient border."""

    def __init__(
        self,
        parent: QWidget | None = None,
        radius: int = 10,
        border_width: int = 2,
        colors: list[str] | None = None,
        animated: bool = True,
        speed: float = 1.0,
    ) -> None:
        super().__init__(parent)
        self._radius = radius
        self._border = border_width
        self._colors = colors or [Colors.VIOLET, Colors.CYAN, Colors.MAGENTA, Colors.VIOLET]
        self._animated = animated
        self._angle = 0.0
        self._speed = speed
        self._active = False

        if animated:
            self._timer = QTimer(self)
            self._timer.setInterval(33)
            self._timer.timeout.connect(self._tick)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active and self._animated:
            self._timer.start()
        else:
            if self._animated:
                self._timer.stop()
            self.update()

    def _tick(self) -> None:
        self._angle = (self._angle + self._speed * 2) % 360
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        cx, cy = rect.width() / 2, rect.height() / 2

        # Outer path (border area)
        outer = QPainterPath()
        outer.addRoundedRect(0, 0, rect.width(), rect.height(), self._radius, self._radius)

        # Inner path (content area)
        inner = QPainterPath()
        b = self._border
        inner.addRoundedRect(b, b, rect.width() - 2*b, rect.height() - 2*b,
                              self._radius - b, self._radius - b)

        border_path = outer - inner

        if self._active:
            grad = QConicalGradient(cx, cy, self._angle)
            n = len(self._colors)
            for i, c in enumerate(self._colors):
                grad.setColorAt(i / (n - 1), QColor(c))
        else:
            grad = QConicalGradient(cx, cy, 0)
            c = QColor(Colors.BORDER_DEFAULT)
            grad.setColorAt(0, c)
            grad.setColorAt(1, c)

        painter.fillPath(border_path, grad)

        # Fill inner with background
        painter.fillPath(inner, QColor(Colors.BG_PANEL))
        painter.end()
