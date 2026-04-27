"""Embedded video player with timeline scrubbing and controls."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QBrush, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QSizePolicy, QFrame,
)

from personacore.gui.theme import Colors


def _try_media_player():
    try:
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PyQt6.QtMultimediaWidgets import QVideoWidget
        return True
    except ImportError:
        return False


HAS_MULTIMEDIA = _try_media_player()


class _NoVideoPlaceholder(QWidget):
    """Shown when no video is loaded."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 240)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        self._t += 0.03
        self.update()

    def paintEvent(self, event) -> None:
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Animated gradient background
        from PyQt6.QtGui import QLinearGradient
        grad = QLinearGradient(0, 0, w, h)
        r1 = QColor(Colors.VIOLET)
        r2 = QColor(Colors.CYAN)
        r1.setAlpha(int(15 + 8 * math.sin(self._t)))
        r2.setAlpha(int(12 + 6 * math.cos(self._t * 0.7)))
        grad.setColorAt(0, r1)
        grad.setColorAt(1, r2)
        painter.fillRect(self.rect(), QBrush(grad))

        # Grid lines
        pen_color = QColor(Colors.BORDER_SUBTLE)
        painter.setPen(pen_color)
        for x in range(0, w, 40):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 40):
            painter.drawLine(0, y, w, y)

        # Center icon
        icon_size = 48
        cx, cy = w // 2, h // 2
        scale = 0.9 + 0.1 * math.sin(self._t * 1.5)
        r = int(icon_size / 2 * scale)

        # Circle
        glow = QColor(Colors.VIOLET)
        glow.setAlpha(int(30 + 20 * math.sin(self._t)))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - r - 8, cy - r - 8, (r + 8) * 2, (r + 8) * 2)

        icon_color = QColor(Colors.VIOLET)
        icon_color.setAlpha(180)
        painter.setBrush(QBrush(icon_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Play triangle
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        tri_size = int(r * 0.55)
        from PyQt6.QtGui import QPolygon
        from PyQt6.QtCore import QPoint
        tri = QPolygon([
            QPoint(cx - tri_size // 2, cy - tri_size),
            QPoint(cx - tri_size // 2, cy + tri_size),
            QPoint(cx + int(tri_size * 0.9), cy),
        ])
        painter.drawPolygon(tri)

        # Text
        painter.setPen(QColor(Colors.TEXT_MUTED))
        painter.setFont(QFont("Inter", 11))
        painter.drawText(self.rect().adjusted(0, r + 30, 0, 0),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                         "Video preview will appear here")

        painter.setPen(QColor(Colors.TEXT_DISABLED))
        painter.setFont(QFont("Inter", 9))
        painter.drawText(self.rect().adjusted(0, r + 50, 0, 0),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                         "Generate a video to preview it")
        painter.end()


class VideoPreviewWidget(QWidget):
    """Video preview panel with playback controls and scrubbing."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._player = None
        self._audio = None
        self._video_widget = None
        self._duration = 0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video area
        self._video_area = QWidget()
        self._video_area.setMinimumSize(400, 240)
        self._video_area.setStyleSheet(f"background: {Colors.BG_DEEP};")
        video_layout = QVBoxLayout(self._video_area)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self._placeholder = _NoVideoPlaceholder()
        video_layout.addWidget(self._placeholder)

        if HAS_MULTIMEDIA:
            from PyQt6.QtMultimediaWidgets import QVideoWidget
            self._video_widget = QVideoWidget()
            self._video_widget.hide()
            self._video_widget.setStyleSheet(f"background: {Colors.BG_DEEP};")
            video_layout.addWidget(self._video_widget)

        layout.addWidget(self._video_area, stretch=1)

        # Controls bar
        controls = QWidget()
        controls.setFixedHeight(52)
        controls.setStyleSheet(f"""
            background: {Colors.BG_PANEL};
            border-top: 1px solid {Colors.BORDER_SUBTLE};
        """)
        ctrl_layout = QVBoxLayout(controls)
        ctrl_layout.setContentsMargins(12, 4, 12, 4)
        ctrl_layout.setSpacing(4)

        # Scrub slider
        self._scrub = QSlider(Qt.Orientation.Horizontal)
        self._scrub.setRange(0, 1000)
        self._scrub.setValue(0)
        self._scrub.sliderMoved.connect(self._on_scrub)
        ctrl_layout.addWidget(self._scrub)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(32, 24)
        self._play_btn.setStyleSheet(self._btn_style(Colors.VIOLET))
        self._play_btn.clicked.connect(self._toggle_play)

        self._stop_btn = QPushButton("■")
        self._stop_btn.setFixedSize(32, 24)
        self._stop_btn.setStyleSheet(self._btn_style(Colors.TEXT_MUTED))
        self._stop_btn.clicked.connect(self._stop)

        self._loop_btn = QPushButton("⟲")
        self._loop_btn.setFixedSize(32, 24)
        self._loop_btn.setCheckable(True)
        self._loop_btn.setStyleSheet(self._btn_style(Colors.CYAN))

        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-family: 'JetBrains Mono';")

        btn_row.addWidget(self._play_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addWidget(self._loop_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._time_label)

        ctrl_layout.addLayout(btn_row)
        layout.addWidget(controls)

        # Timer for updating scrubber
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(200)
        self._update_timer.timeout.connect(self._update_position)

    def _btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background: {color}22;
                border: 1px solid {color}55;
                border-radius: 4px;
                color: {color};
                font-size: 11px;
            }}
            QPushButton:hover {{ background: {color}44; }}
            QPushButton:checked {{ background: {color}66; border-color: {color}; }}
        """

    def load_video(self, path: Path) -> None:
        if not path.exists():
            return

        if HAS_MULTIMEDIA and self._video_widget:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

            if self._player:
                self._player.stop()
                self._player.deleteLater()

            self._player = QMediaPlayer(self)
            self._audio = QAudioOutput(self)
            self._player.setAudioOutput(self._audio)
            self._player.setVideoOutput(self._video_widget)
            self._player.durationChanged.connect(self._on_duration)
            self._player.playbackStateChanged.connect(self._on_state_changed)
            self._player.setSource(QUrl.fromLocalFile(str(path.absolute())))

            self._placeholder.hide()
            self._video_widget.show()
            self._player.play()
            self._update_timer.start()
        else:
            # Show path in placeholder
            self._placeholder.setToolTip(str(path))

    def _toggle_play(self) -> None:
        if not self._player:
            return
        from PyQt6.QtMultimedia import QMediaPlayer
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("▶")
        else:
            self._player.play()
            self._play_btn.setText("⏸")

    def _stop(self) -> None:
        if self._player:
            self._player.stop()
            self._play_btn.setText("▶")

    def _on_scrub(self, value: int) -> None:
        if self._player and self._duration:
            pos = int(value / 1000 * self._duration)
            self._player.setPosition(pos)

    def _on_duration(self, duration: int) -> None:
        self._duration = duration

    def _on_state_changed(self, state) -> None:
        from PyQt6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_btn.setText("⏸")
        else:
            self._play_btn.setText("▶")
            if self._loop_btn.isChecked() and self._player:
                if self._player.position() >= self._duration - 100:
                    self._player.setPosition(0)
                    self._player.play()

    def _update_position(self) -> None:
        if not self._player or not self._duration:
            return
        pos = self._player.position()
        frac = pos / self._duration if self._duration else 0
        self._scrub.setValue(int(frac * 1000))
        p_s = pos // 1000
        d_s = self._duration // 1000
        self._time_label.setText(f"{p_s//60}:{p_s%60:02d} / {d_s//60}:{d_s%60:02d}")
