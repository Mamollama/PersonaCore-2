"""Custom animated buttons with glow effects."""

from __future__ import annotations

import math

from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen, QFont
from PyQt6.QtWidgets import QPushButton, QWidget

from personacore.gui.theme import Colors


class AnimatedButton(QPushButton):
    """Button with smooth hover animation."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._hover_progress = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._animate)
        self._hovering = False
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event) -> None:
        self._hovering = True
        self._timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovering = False
        self._timer.start()
        super().leaveEvent(event)

    def _animate(self) -> None:
        target = 1.0 if self._hovering else 0.0
        self._hover_progress += (target - self._hover_progress) * 0.2
        if abs(self._hover_progress - target) < 0.01:
            self._hover_progress = target
            self._timer.stop()
        self.update()


class GlowButton(AnimatedButton):
    """Premium glow button with animated gradient border."""

    def __init__(
        self,
        text: str = "",
        glow_color: str = Colors.VIOLET,
        filled: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._glow_color = QColor(glow_color)
        self._filled = filled
        self._t = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(33)
        self._pulse_timer.timeout.connect(self._pulse)
        self.setMinimumHeight(38)
        self.setFont(QFont("Inter", 11, QFont.Weight.DemiBold))
        self.setFlat(True)

    def start_pulse(self) -> None:
        self._pulse_timer.start()

    def stop_pulse(self) -> None:
        self._pulse_timer.stop()
        self._t = 0.0
        self.update()

    def _pulse(self) -> None:
        self._t += 0.08
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 8, 8)

        h = self._hover_progress
        glow_alpha = int(40 + h * 80 + math.sin(self._t) * 20)

        if self._filled:
            # Gradient fill
            grad = QLinearGradient(0, 0, rect.width(), 0)
            c1 = QColor(self._glow_color)
            c2 = QColor(Colors.CYAN)
            c1.setAlpha(int(200 + h * 55))
            c2.setAlpha(int(180 + h * 75))
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            painter.fillPath(path, QBrush(grad))
        else:
            # Transparent with border
            bg = QColor(self._glow_color)
            bg.setAlpha(glow_alpha)
            painter.fillPath(path, QBrush(bg))

        # Glow border
        glow = QColor(self._glow_color)
        glow.setAlpha(int(100 + h * 155 + math.sin(self._t) * 40))
        pen = QPen(glow, 1.5)
        painter.setPen(pen)
        painter.drawPath(path)

        # Text
        text_color = QColor("#FFFFFF") if self._filled else self._glow_color
        text_color.setAlpha(int(220 + h * 35))
        painter.setPen(text_color)
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()
