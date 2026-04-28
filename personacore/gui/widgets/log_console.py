"""Color-coded live log console panel."""

from __future__ import annotations

import logging

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from personacore.gui.theme import Colors

_LEVEL_COLORS = {
    logging.DEBUG:    Colors.LOG_DEBUG,
    logging.INFO:     Colors.LOG_INFO,
    logging.WARNING:  Colors.LOG_WARNING,
    logging.ERROR:    Colors.LOG_ERROR,
    logging.CRITICAL: Colors.LOG_CRITICAL,
}

_LEVEL_LABELS = {
    logging.DEBUG:    "DBG",
    logging.INFO:     "INF",
    logging.WARNING:  "WRN",
    logging.ERROR:    "ERR",
    logging.CRITICAL: "CRT",
}

MAX_LINES = 500


class LogConsole(QWidget):
    """Collapsible color-coded log console."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._paused = False
        self._pending: list[tuple[int, str, str]] = []
        self._line_count = 0
        self._collapsed = False
        self._build_ui()

        # Flush pending logs at 30fps
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(33)
        self._flush_timer.timeout.connect(self._flush_pending)
        self._flush_timer.start()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet(f"""
            background: {Colors.BG_SURFACE};
            border-top: 1px solid {Colors.BORDER_SUBTLE};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 8, 0)
        header_layout.setSpacing(8)

        self._toggle_btn = QPushButton("▼")
        self._toggle_btn.setFixedSize(20, 20)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_MUTED};
                font-size: 10px;
            }}
            QPushButton:hover {{ color: {Colors.TEXT_PRIMARY}; }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_collapsed)
        header_layout.addWidget(self._toggle_btn)

        title = QLabel("CONSOLE")
        title.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1.5px;
        """)
        header_layout.addWidget(title)

        self._count_lbl = QLabel("0 lines")
        self._count_lbl.setStyleSheet(f"color: {Colors.TEXT_DISABLED}; font-size: 8px;")
        header_layout.addWidget(self._count_lbl)

        header_layout.addStretch()

        # Pause/resume
        self._pause_btn = QPushButton("⏸")
        self._pause_btn.setFixedSize(24, 20)
        self._pause_btn.setCheckable(True)
        self._pause_btn.setToolTip("Pause auto-scroll")
        self._pause_btn.setStyleSheet(self._icon_btn_style())
        self._pause_btn.toggled.connect(self._on_pause_toggled)
        header_layout.addWidget(self._pause_btn)

        # Copy
        copy_btn = QPushButton("⎘")
        copy_btn.setFixedSize(24, 20)
        copy_btn.setToolTip("Copy to clipboard")
        copy_btn.setStyleSheet(self._icon_btn_style())
        copy_btn.clicked.connect(self._copy_all)
        header_layout.addWidget(copy_btn)

        # Clear
        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(24, 20)
        clear_btn.setToolTip("Clear console")
        clear_btn.setStyleSheet(self._icon_btn_style())
        clear_btn.clicked.connect(self._clear)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # Log area
        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setMaximumHeight(180)
        self._log_area.setFont(QFont("JetBrains Mono", 9))
        self._log_area.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.BG_DEEP};
                color: {Colors.TEXT_SECONDARY};
                border: none;
                padding: 6px 10px;
                font-size: 9px;
                selection-background-color: {Colors.VIOLET};
            }}
        """)
        self._log_area.enterEvent = self._on_enter
        self._log_area.leaveEvent = self._on_leave

        layout.addWidget(self._log_area)

    def _icon_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_MUTED};
                font-size: 10px;
            }}
            QPushButton:hover {{ color: {Colors.TEXT_PRIMARY}; }}
            QPushButton:checked {{ color: {Colors.CYAN}; }}
        """

    def _toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        self._log_area.setVisible(not self._collapsed)
        self._toggle_btn.setText("▶" if self._collapsed else "▼")

    def _on_pause_toggled(self, checked: bool) -> None:
        self._paused = checked

    def _on_enter(self, event) -> None:
        self._paused = True
        QTextEdit.enterEvent(self._log_area, event)

    def _on_leave(self, event) -> None:
        if not self._pause_btn.isChecked():
            self._paused = False
        QTextEdit.leaveEvent(self._log_area, event)

    def append_log(self, level: int, name: str, message: str) -> None:
        self._pending.append((level, name, message))

    def _flush_pending(self) -> None:
        if not self._pending:
            return
        batch = self._pending[:50]
        self._pending = self._pending[50:]

        cursor = self._log_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        for level, name, message in batch:
            color = _LEVEL_COLORS.get(level, Colors.TEXT_SECONDARY)

            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))

            cursor.insertText(message + "\n", fmt)
            self._line_count += 1

        # Trim excess lines
        doc = self._log_area.document()
        while doc.blockCount() > MAX_LINES:
            tc = QTextCursor(doc.begin())
            tc.select(QTextCursor.SelectionType.BlockUnderCursor)
            tc.removeSelectedText()
            tc.deleteChar()  # remove block separator

        self._count_lbl.setText(f"{self._line_count} lines")

        if not self._paused:
            self._log_area.moveCursor(QTextCursor.MoveOperation.End)
            self._log_area.ensureCursorVisible()

    def _copy_all(self) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._log_area.toPlainText())

    def _clear(self) -> None:
        self._log_area.clear()
        self._line_count = 0
        self._count_lbl.setText("0 lines")
