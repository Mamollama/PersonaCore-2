"""Visual pipeline step tracker with timing and pulse animations."""

from __future__ import annotations

import time
from dataclasses import dataclass

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from personacore.gui.theme import Colors

STEPS = [
    ("enrich",    "Enriching",   Colors.VIOLET),
    ("generating","Generating",  Colors.CYAN),
    ("processing","Processing",  Colors.MAGENTA),
    ("rendering", "Rendering",   Colors.WARNING),
    ("complete",  "Complete",    Colors.SUCCESS),
]

STEP_IDS = [s[0] for s in STEPS]


@dataclass
class StepState:
    id: str
    label: str
    color: str
    status: str = "idle"   # idle | active | done | error | cancelled
    elapsed: float = 0.0
    start_time: float | None = None


class _StepDot(QWidget):
    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._status = "idle"
        self._t = 0.0
        self.setFixedSize(16, 16)

    def set_status(self, status: str) -> None:
        self._status = status
        self.update()

    def set_t(self, t: float) -> None:
        self._t = t
        self.update()

    def paintEvent(self, event) -> None:
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = 8, 8, 6

        if self._status == "idle":
            c = QColor(Colors.BG_ELEVATED)
            painter.setBrush(QBrush(c))
            painter.setPen(QPen(QColor(Colors.BORDER_DEFAULT), 1.5))
            painter.drawEllipse(cx - r, cy - r, r*2, r*2)

        elif self._status == "active":
            # Pulsing glow
            pulse = 0.6 + 0.4 * math.sin(self._t * 4)
            glow = QColor(self._color)
            glow.setAlphaF(0.25 * pulse)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - 8, cy - 8, 16, 16)

            # Core
            painter.setBrush(QBrush(self._color))
            painter.setPen(QPen(self._color.lighter(150), 1))
            pr = int(r * (0.8 + 0.2 * pulse))
            painter.drawEllipse(cx - pr, cy - pr, pr*2, pr*2)

        elif self._status == "done":
            painter.setBrush(QBrush(QColor(Colors.SUCCESS)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - r, cy - r, r*2, r*2)
            # Checkmark
            painter.setPen(QPen(QColor("#000000"), 1.5))
            painter.drawLine(cx - 3, cy, cx - 1, cy + 2)
            painter.drawLine(cx - 1, cy + 2, cx + 3, cy - 2)

        elif self._status == "error":
            painter.setBrush(QBrush(QColor(Colors.ERROR)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - r, cy - r, r*2, r*2)
            painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
            painter.drawLine(cx - 2, cy - 2, cx + 2, cy + 2)
            painter.drawLine(cx + 2, cy - 2, cx - 2, cy + 2)

        elif self._status == "cancelled":
            c = QColor(Colors.WARNING)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - r, cy - r, r*2, r*2)

        painter.end()


class StepTracker(QWidget):
    """Horizontal pipeline step indicator."""

    cancelled = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._steps: list[StepState] = [
            StepState(id=sid, label=label, color=color)
            for sid, label, color in STEPS
        ]
        self._current_idx = -1
        self._t = 0.0
        self._dots: list[_StepDot] = []
        self._time_labels: list[QLabel] = []
        self._status_labels: list[QLabel] = []

        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        for i, step in enumerate(self._steps):
            step_w = QWidget()
            step_layout = QVBoxLayout(step_w)
            step_layout.setContentsMargins(4, 0, 4, 0)
            step_layout.setSpacing(3)
            step_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            dot = _StepDot(step.color)
            self._dots.append(dot)
            step_layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignHCenter)

            lbl = QLabel(step.label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px;")
            self._status_labels.append(lbl)
            step_layout.addWidget(lbl)

            tlbl = QLabel("")
            tlbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            tlbl.setStyleSheet(
                f"color: {Colors.TEXT_DISABLED}; font-size: 8px; "
                "font-family: 'JetBrains Mono';"
            )
            self._time_labels.append(tlbl)
            step_layout.addWidget(tlbl)

            row_layout.addWidget(step_w)

            # Connector line
            if i < len(self._steps) - 1:
                line = QWidget()
                line.setFixedSize(20, 2)
                line.setStyleSheet(f"background: {Colors.BORDER_SUBTLE}; border-radius: 1px;")
                row_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(row)

    def set_step(self, step_id: str) -> None:
        if step_id == "cancelled":
            self._mark_cancelled()
            return

        for i, s in enumerate(self._steps):
            if s.id == step_id:
                # Mark previous steps done
                for j in range(i):
                    self._steps[j].status = "done"
                    self._dots[j].set_status("done")
                    self._status_labels[j].setStyleSheet(
                        f"color: {Colors.SUCCESS}; font-size: 9px;"
                    )
                # Activate current
                s.status = "active"
                s.start_time = time.time()
                self._dots[i].set_status("active")
                self._status_labels[i].setStyleSheet(
                    f"color: {s.color}; font-size: 9px; font-weight: 600;"
                )
                # Reset future
                for j in range(i + 1, len(self._steps)):
                    self._steps[j].status = "idle"
                    self._dots[j].set_status("idle")
                    self._status_labels[j].setStyleSheet(
                        f"color: {Colors.TEXT_MUTED}; font-size: 9px;"
                    )
                    self._time_labels[j].setText("")

                self._current_idx = i
                self._timer.start()
                return

    def set_complete(self) -> None:
        self._timer.stop()
        for i, s in enumerate(self._steps):
            s.status = "done"
            self._dots[i].set_status("done")
            self._status_labels[i].setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 9px;")

    def set_error(self, step_id: str | None = None) -> None:
        self._timer.stop()
        target_id = step_id or (
            self._steps[self._current_idx].id if self._current_idx >= 0 else None
        )
        for i, s in enumerate(self._steps):
            if s.id == target_id:
                s.status = "error"
                self._dots[i].set_status("error")
                self._status_labels[i].setStyleSheet(f"color: {Colors.ERROR}; font-size: 9px;")

    def reset(self) -> None:
        self._timer.stop()
        self._current_idx = -1
        self._t = 0.0
        for i, s in enumerate(self._steps):
            s.status = "idle"
            s.start_time = None
            s.elapsed = 0.0
            self._dots[i].set_status("idle")
            self._status_labels[i].setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px;")
            self._time_labels[i].setText("")

    def _mark_cancelled(self) -> None:
        self._timer.stop()
        if self._current_idx >= 0:
            s = self._steps[self._current_idx]
            s.status = "cancelled"
            self._dots[self._current_idx].set_status("cancelled")
            self._status_labels[self._current_idx].setStyleSheet(
                f"color: {Colors.WARNING}; font-size: 9px;"
            )

    def _tick(self) -> None:
        self._t += 0.05
        if self._current_idx >= 0:
            s = self._steps[self._current_idx]
            if s.start_time:
                elapsed = time.time() - s.start_time
                self._time_labels[self._current_idx].setText(f"{elapsed:.1f}s")
            self._dots[self._current_idx].set_t(self._t)
