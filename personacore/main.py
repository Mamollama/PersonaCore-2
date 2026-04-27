"""PersonaCore 2 application entry point."""

from __future__ import annotations

import sys
import os


def main() -> None:
    # High-DPI support must be set before QApplication
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt, QCoreApplication
    from PyQt6.QtGui import QIcon

    QCoreApplication.setApplicationName("PersonaCore 2")
    QCoreApplication.setOrganizationName("PersonaCore")
    QCoreApplication.setApplicationVersion("2.0.0")

    app = QApplication(sys.argv)

    from personacore.gui.theme import apply_theme
    apply_theme(app)

    from personacore.gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
