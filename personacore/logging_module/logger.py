"""Structured application logger with Qt signal emission for UI log console."""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import IntEnum

from PyQt6.QtCore import QObject, pyqtSignal


class LogLevel(IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class _QtLogHandler(logging.Handler, QObject):
    """Bridge between Python's logging and Qt signals."""

    log_emitted = pyqtSignal(int, str, str)  # level, name, message

    def __init__(self) -> None:
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.log_emitted.emit(record.levelno, record.name, msg)
        except Exception:  # noqa: BLE001
            self.handleError(record)


class AppLogger(QObject):
    """Central application logger. Singleton accessed via get_logger()."""

    log_emitted = pyqtSignal(int, str, str)  # level, name, message

    _instance: AppLogger | None = None

    def __new__(cls) -> AppLogger:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Ensure proper initialization order
        super().__init__()
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._root = logging.getLogger("personacore")
        self._root.setLevel(logging.DEBUG)

        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )

        self._handler = logging.StreamHandler()
        self._handler.setFormatter(fmt)
        self._root.addHandler(self._handler)

        qt_handler = _QtLogHandler()
        qt_handler.setFormatter(fmt)
        qt_handler.log_emitted.connect(self.log_emitted)
        self._root.addHandler(qt_handler)

        self._callbacks: list[Callable[[int, str, str], None]] = []

    def get(self, name: str) -> logging.Logger:
        return logging.getLogger(f"personacore.{name}")

    def set_level(self, level: LogLevel) -> None:
        self._root.setLevel(int(level))

    def add_callback(self, cb: Callable[[int, str, str], None]) -> None:
        self._callbacks.append(cb)


_app_logger: AppLogger | None = None


def get_logger(name: str = "app") -> logging.Logger:
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger()
    return _app_logger.get(name)


def get_app_logger() -> AppLogger:
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger()
    return _app_logger
