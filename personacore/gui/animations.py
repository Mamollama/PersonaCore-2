"""Reusable Qt animation helpers for the PersonaCore 2 UI."""

from __future__ import annotations

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, QTimer, pyqtProperty, QObject,
    Qt, QRect,
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect


def fade_in(widget: QWidget, duration: int = 250) -> QPropertyAnimation:
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    return anim


def fade_out(widget: QWidget, duration: int = 200, then_hide: bool = True) -> QPropertyAnimation:
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.Type.InCubic)
    if then_hide:
        anim.finished.connect(widget.hide)
    anim.start()
    return anim


def slide_in(widget: QWidget, direction: str = "left", duration: int = 300) -> QPropertyAnimation:
    anim = QPropertyAnimation(widget, b"geometry", widget)
    anim.setDuration(duration)
    anim.setEasingCurve(QEasingCurve.Type.OutExpo)
    geo = widget.geometry()
    if direction == "left":
        start = QRect(geo.x() - geo.width(), geo.y(), geo.width(), geo.height())
    elif direction == "right":
        start = QRect(geo.x() + geo.width(), geo.y(), geo.width(), geo.height())
    elif direction == "up":
        start = QRect(geo.x(), geo.y() - geo.height(), geo.width(), geo.height())
    else:
        start = QRect(geo.x(), geo.y() + geo.height(), geo.width(), geo.height())
    anim.setStartValue(start)
    anim.setEndValue(geo)
    anim.start()
    return anim


class PulseAnimation(QObject):
    """Repeatedly pulses a widget's opacity to indicate activity."""

    def __init__(self, widget: QWidget, min_opacity: float = 0.4, period: int = 1200) -> None:
        super().__init__(widget)
        self._effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self._effect)

        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(period // 2)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(min_opacity)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)  # infinite

        seq = QSequentialAnimationGroup(self)
        fwd = QPropertyAnimation(self._effect, b"opacity", seq)
        fwd.setDuration(period // 2)
        fwd.setStartValue(1.0)
        fwd.setEndValue(min_opacity)
        fwd.setEasingCurve(QEasingCurve.Type.InOutSine)

        bwd = QPropertyAnimation(self._effect, b"opacity", seq)
        bwd.setDuration(period // 2)
        bwd.setStartValue(min_opacity)
        bwd.setEndValue(1.0)
        bwd.setEasingCurve(QEasingCurve.Type.InOutSine)

        seq.addAnimation(fwd)
        seq.addAnimation(bwd)
        seq.setLoopCount(-1)
        self._seq = seq

    def start(self) -> None:
        self._seq.start()

    def stop(self) -> None:
        self._seq.stop()
        self._effect.setOpacity(1.0)


class GlowTimer(QObject):
    """Drives animated glow border by emitting tick signals."""
    def __init__(self, interval: int = 50, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(interval)
        self._timer.timeout.connect(self._tick)
        self._callbacks: list = []

    def _tick(self) -> None:
        import math
        self._t += 0.05
        for cb in self._callbacks:
            cb(self._t)

    def add_callback(self, cb) -> None:
        self._callbacks.append(cb)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
