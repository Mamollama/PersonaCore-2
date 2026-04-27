"""Custom frameless window title bar with dragging and window controls."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QFont
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)

from personacore.gui.theme import Colors


class _WinButton(QPushButton):
    def __init__(self, symbol: str, color: str, parent=None) -> None:
        super().__init__(symbol, parent)
        self._color = color
        self.setFixedSize(16, 16)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {color}33;
                border: 1px solid {color}66;
                border-radius: 8px;
                color: transparent;
                font-size: 8px;
            }}
            QPushButton:hover {{
                background: {color};
                color: #000000BB;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class TitleBar(QWidget):
    """Custom draggable title bar for frameless window."""

    close_requested = pyqtSignal()
    minimize_requested = pyqtSignal()
    maximize_requested = pyqtSignal()

    def __init__(self, title: str = "PersonaCore 2", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("TitleBar")

        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 12, 0)
        layout.setSpacing(8)

        # Logo mark
        logo = QLabel("◈")
        logo.setStyleSheet(f"""
            color: {Colors.VIOLET};
            font-size: 16px;
            font-weight: 900;
        """)
        layout.addWidget(logo)

        # App title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(title_label)

        # Tagline
        tag = QLabel("AI VIDEO SUITE")
        tag.setStyleSheet(f"""
            color: {Colors.VIOLET};
            font-size: 8px;
            font-weight: 700;
            letter-spacing: 2px;
            margin-top: 3px;
        """)
        layout.addWidget(tag)

        layout.addStretch()

        # Window controls (macOS-style circles)
        for sym, color, sig in [
            ("✕", "#FF5F56", self.close_requested),
            ("−", "#FFBD2E", self.minimize_requested),
            ("⤢", "#27C93F", self.maximize_requested),
        ]:
            btn = _WinButton(sym, color)
            btn.clicked.connect(sig.emit)
            layout.addWidget(btn)

        self.setStyleSheet(f"""
            QWidget#TitleBar {{
                background-color: {Colors.BG_DEEP};
                border-bottom: 1px solid {Colors.BORDER_SUBTLE};
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            window = self.window()
            delta = event.globalPosition().toPoint() - self._drag_pos
            window.move(window.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event) -> None:
        self.maximize_requested.emit()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(Colors.VIOLET + "22"))
        grad.setColorAt(0.5, QColor(Colors.BG_DEEP))
        grad.setColorAt(1, QColor(Colors.CYAN + "11"))
        painter.fillRect(self.rect(), QBrush(grad))
        super().paintEvent(event)
