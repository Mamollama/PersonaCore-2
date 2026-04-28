"""Dark cinematic theme engine for PersonaCore 2."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PyQt6.QtWidgets import QApplication

# ─── Color Palette ──────────────────────────────────────────────────────────

class Colors:
    # Backgrounds
    BG_DEEP      = "#0A0A0F"
    BG_BASE      = "#0D0D14"
    BG_PANEL     = "#111119"
    BG_SURFACE   = "#16161F"
    BG_ELEVATED  = "#1C1C28"
    BG_HOVER     = "#22222F"
    BG_ACTIVE    = "#2A2A3C"

    # Borders
    BORDER_SUBTLE  = "#1E1E2E"
    BORDER_DEFAULT = "#2A2A3E"
    BORDER_FOCUS   = "#6E3BFF"

    # Accent — Electric Violet
    VIOLET       = "#6E3BFF"
    VIOLET_LIGHT  = "#8A5FFF"
    VIOLET_DARK   = "#5020DD"
    VIOLET_GLOW   = "#6E3BFF44"

    # Accent — Cyan
    CYAN         = "#00E5FF"
    CYAN_LIGHT   = "#40EEFF"
    CYAN_DARK    = "#00B8CC"
    CYAN_GLOW    = "#00E5FF33"

    # Accent — Magenta
    MAGENTA      = "#FF2D78"
    MAGENTA_LIGHT = "#FF5A95"
    MAGENTA_DARK  = "#CC1055"
    MAGENTA_GLOW  = "#FF2D7833"

    # Text
    TEXT_PRIMARY   = "#F0F0FF"
    TEXT_SECONDARY = "#9090B0"
    TEXT_MUTED     = "#606080"
    TEXT_DISABLED  = "#404055"

    # Status
    SUCCESS  = "#00FF88"
    WARNING  = "#FFB300"
    ERROR    = "#FF2D78"
    INFO     = "#00E5FF"

    # Log levels
    LOG_DEBUG   = "#606080"
    LOG_INFO    = "#00E5FF"
    LOG_WARNING = "#FFB300"
    LOG_ERROR   = "#FF2D78"
    LOG_CRITICAL = "#FF0000"


class Fonts:
    PRIMARY_FAMILY = "Inter"
    MONO_FAMILY = "JetBrains Mono"

    SIZE_XS  = 9
    SIZE_SM  = 10
    SIZE_BASE = 11
    SIZE_MD  = 13
    SIZE_LG  = 15
    SIZE_XL  = 18
    SIZE_2XL = 24
    SIZE_3XL = 32

    _loaded = False

    @classmethod
    def load(cls) -> None:
        if cls._loaded:
            return
        assets = Path(__file__).parent.parent.parent / "assets" / "fonts"
        if assets.exists():
            for ttf in assets.glob("*.ttf"):
                QFontDatabase.addApplicationFont(str(ttf))
            for otf in assets.glob("*.otf"):
                QFontDatabase.addApplicationFont(str(otf))
        cls._loaded = True

    @classmethod
    def primary(cls, size: int = SIZE_BASE, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
        f = QFont(cls.PRIMARY_FAMILY, size)
        f.setWeight(weight)
        f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        return f

    @classmethod
    def mono(cls, size: int = SIZE_BASE, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
        f = QFont(cls.MONO_FAMILY, size)
        f.setWeight(weight)
        f.setFixedPitch(True)
        return f

    @classmethod
    def heading(cls, size: int = SIZE_LG) -> QFont:
        return cls.primary(size, QFont.Weight.DemiBold)

    @classmethod
    def title(cls, size: int = SIZE_XL) -> QFont:
        return cls.primary(size, QFont.Weight.Bold)


GLOBAL_STYLESHEET = f"""
/* ═══════════════════════════════ Base ═════════════════════════════════ */
QWidget {{
    background-color: {Colors.BG_BASE};
    color: {Colors.TEXT_PRIMARY};
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 11px;
    selection-background-color: {Colors.VIOLET};
    selection-color: {Colors.TEXT_PRIMARY};
    border: none;
    outline: none;
}}

QMainWindow {{
    background-color: {Colors.BG_DEEP};
}}

/* ═══════════════════════════════ Scrollbars ════════════════════════════ */
QScrollBar:vertical {{
    background: {Colors.BG_BASE};
    width: 6px;
    margin: 0;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {Colors.BG_ELEVATED};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Colors.VIOLET};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {Colors.BG_BASE};
    height: 6px;
    margin: 0;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {Colors.BG_ELEVATED};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {Colors.VIOLET};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ═══════════════════════════════ Buttons ═══════════════════════════════ */
QPushButton {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 11px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {Colors.BG_HOVER};
    border-color: {Colors.VIOLET};
    color: {Colors.TEXT_PRIMARY};
}}
QPushButton:pressed {{
    background-color: {Colors.BG_ACTIVE};
    border-color: {Colors.VIOLET_LIGHT};
}}
QPushButton:disabled {{
    color: {Colors.TEXT_DISABLED};
    border-color: {Colors.BORDER_SUBTLE};
}}

QPushButton[accent="violet"] {{
    background-color: {Colors.VIOLET};
    border-color: {Colors.VIOLET_LIGHT};
    color: white;
    font-weight: 600;
}}
QPushButton[accent="violet"]:hover {{
    background-color: {Colors.VIOLET_LIGHT};
}}
QPushButton[accent="violet"]:pressed {{
    background-color: {Colors.VIOLET_DARK};
}}

QPushButton[accent="cyan"] {{
    background-color: transparent;
    border: 1px solid {Colors.CYAN};
    color: {Colors.CYAN};
    font-weight: 600;
}}
QPushButton[accent="cyan"]:hover {{
    background-color: {Colors.CYAN_GLOW};
    color: {Colors.CYAN_LIGHT};
}}

QPushButton[accent="danger"] {{
    background-color: transparent;
    border: 1px solid {Colors.MAGENTA};
    color: {Colors.MAGENTA};
}}
QPushButton[accent="danger"]:hover {{
    background-color: {Colors.MAGENTA_GLOW};
}}

/* ═══════════════════════════════ Text Inputs ═══════════════════════════ */
QTextEdit, QPlainTextEdit {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 8px;
    padding: 10px;
    font-size: 11px;
    line-height: 1.5;
    selection-background-color: {Colors.VIOLET};
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {Colors.VIOLET};
}}

QLineEdit {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
}}
QLineEdit:focus {{
    border-color: {Colors.VIOLET};
    background-color: {Colors.BG_ELEVATED};
}}

/* ═══════════════════════════════ ComboBox ══════════════════════════════ */
QComboBox {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 6px;
    padding: 6px 32px 6px 10px;
    font-size: 11px;
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: {Colors.VIOLET};
}}
QComboBox:focus {{
    border-color: {Colors.VIOLET};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {Colors.TEXT_SECONDARY};
    width: 0;
    height: 0;
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_FOCUS};
    border-radius: 6px;
    selection-background-color: {Colors.VIOLET};
    outline: none;
    padding: 4px;
}}

/* ═══════════════════════════════ Sliders ═══════════════════════════════ */
QSlider::groove:horizontal {{
    background: {Colors.BG_ELEVATED};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {Colors.VIOLET};
    border: 2px solid {Colors.VIOLET_LIGHT};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {Colors.VIOLET_LIGHT};
    border-color: {Colors.CYAN};
}}
QSlider::sub-page:horizontal {{
    background: {Colors.VIOLET};
    border-radius: 2px;
}}

/* ═══════════════════════════════ SpinBox ═══════════════════════════════ */
QSpinBox, QDoubleSpinBox {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 11px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {Colors.VIOLET};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    background: {Colors.BG_ELEVATED};
    border: none;
    border-radius: 3px;
    width: 18px;
    margin: 2px 2px 1px 0;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {Colors.BG_ELEVATED};
    border: none;
    border-radius: 3px;
    width: 18px;
    margin: 1px 2px 2px 0;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {Colors.VIOLET};
}}

/* ═══════════════════════════════ Labels ════════════════════════════════ */
QLabel {{
    color: {Colors.TEXT_PRIMARY};
    background: transparent;
}}
QLabel[role="title"] {{
    color: {Colors.TEXT_PRIMARY};
    font-size: 14px;
    font-weight: 700;
}}
QLabel[role="subtitle"] {{
    color: {Colors.TEXT_SECONDARY};
    font-size: 10px;
    font-weight: 400;
}}
QLabel[role="section"] {{
    color: {Colors.TEXT_SECONDARY};
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1px;
}}
QLabel[role="accent"] {{
    color: {Colors.VIOLET};
}}
QLabel[role="cyan"] {{
    color: {Colors.CYAN};
}}

/* ═══════════════════════════════ Tabs ══════════════════════════════════ */
QTabWidget::pane {{
    background-color: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER_SUBTLE};
    border-radius: 8px;
}}
QTabBar::tab {{
    background: transparent;
    color: {Colors.TEXT_SECONDARY};
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 11px;
    font-weight: 500;
}}
QTabBar::tab:hover {{
    color: {Colors.TEXT_PRIMARY};
    background: {Colors.BG_HOVER};
}}
QTabBar::tab:selected {{
    color: {Colors.VIOLET_LIGHT};
    border-bottom: 2px solid {Colors.VIOLET};
}}

/* ═══════════════════════════════ GroupBox ══════════════════════════════ */
QGroupBox {{
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 8px;
    margin-top: 18px;
    padding: 12px;
    font-size: 10px;
    font-weight: 600;
    color: {Colors.TEXT_SECONDARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {Colors.TEXT_SECONDARY};
    letter-spacing: 0.5px;
}}

/* ═══════════════════════════════ Progress Bar ══════════════════════════ */
QProgressBar {{
    background-color: {Colors.BG_ELEVATED};
    border: 1px solid {Colors.BORDER_SUBTLE};
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {Colors.VIOLET},
        stop:0.5 {Colors.CYAN},
        stop:1 {Colors.MAGENTA});
    border-radius: 4px;
}}

/* ═══════════════════════════════ Splitter ══════════════════════════════ */
QSplitter::handle {{
    background: {Colors.BORDER_SUBTLE};
    width: 2px;
    height: 2px;
}}
QSplitter::handle:hover {{
    background: {Colors.VIOLET};
}}

/* ═══════════════════════════════ CheckBox ══════════════════════════════ */
QCheckBox {{
    color: {Colors.TEXT_PRIMARY};
    font-size: 11px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 4px;
    background: {Colors.BG_SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {Colors.VIOLET};
    border-color: {Colors.VIOLET_LIGHT};
}}
QCheckBox::indicator:hover {{
    border-color: {Colors.VIOLET};
}}

/* ═══════════════════════════════ ToolTip ═══════════════════════════════ */
QToolTip {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_FOCUS};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10px;
}}

/* ═══════════════════════════════ Menu ══════════════════════════════════ */
QMenu {{
    background-color: {Colors.BG_ELEVATED};
    border: 1px solid {Colors.BORDER_FOCUS};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
    color: {Colors.TEXT_PRIMARY};
    font-size: 11px;
}}
QMenu::item:selected {{
    background-color: {Colors.VIOLET};
}}
QMenu::separator {{
    height: 1px;
    background: {Colors.BORDER_SUBTLE};
    margin: 4px 8px;
}}

/* ═══════════════════════════════ StatusBar ═════════════════════════════ */
QStatusBar {{
    background: {Colors.BG_DEEP};
    border-top: 1px solid {Colors.BORDER_SUBTLE};
    color: {Colors.TEXT_MUTED};
    font-size: 10px;
    padding: 2px 8px;
}}

/* ═══════════════════════════════ List Views ════════════════════════════ */
QListWidget, QTreeWidget {{
    background: {Colors.BG_PANEL};
    border: 1px solid {Colors.BORDER_SUBTLE};
    border-radius: 6px;
    outline: none;
    padding: 4px;
}}
QListWidget::item, QTreeWidget::item {{
    padding: 6px 8px;
    border-radius: 4px;
    color: {Colors.TEXT_PRIMARY};
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background: {Colors.BG_HOVER};
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {Colors.VIOLET};
    color: white;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply the full dark cinematic theme to the application."""
    Fonts.load()
    app.setStyleSheet(GLOBAL_STYLESHEET)
    app.setFont(Fonts.primary())

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_BASE))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_PANEL))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.BG_ELEVATED))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.VIOLET))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Link, QColor(Colors.CYAN))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.BG_ELEVATED))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.TEXT_PRIMARY))
    app.setPalette(palette)
