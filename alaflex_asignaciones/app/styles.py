from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from app.theme import (
    BUTTON_HEIGHT,
    CARD_RADIUS,
    COLOR_BG,
    COLOR_BLUE,
    COLOR_BLUE_HOVER,
    COLOR_BORDER,
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_NAVY,
    COLOR_NAVY_DARK,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    FONT_FAMILY,
    TABLE_ROW_HEIGHT,
)


def rgba(hex_color: str, alpha: float) -> str:
    value = hex_color.lstrip("#")
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha})"


GLOBAL_STYLES = f"""
* {{
    font-family: "{FONT_FAMILY}";
    color: {COLOR_TEXT};
}}

QMainWindow, QWidget#Root {{
    background: {COLOR_BG};
}}

QFrame#Card {{
    background: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {CARD_RADIUS}px;
}}

QLabel#AppTitle {{
    color: {COLOR_TEXT};
    font-size: 32px;
    font-weight: 800;
}}

QLabel#ModuleTitle {{
    color: {COLOR_TEXT};
    font-size: 25px;
    font-weight: 800;
}}

QLabel#Subtitle {{
    color: {COLOR_TEXT_MUTED};
    font-size: 15px;
}}

QLabel#SectionTitle {{
    color: {COLOR_TEXT};
    font-size: 18px;
    font-weight: 800;
}}

QLineEdit, QComboBox {{
    min-height: 44px;
    padding-left: 14px;
    padding-right: 14px;
    background: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    font-size: 14px;
    color: {COLOR_TEXT};
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {COLOR_BLUE};
}}

QLineEdit::placeholder {{
    color: #9AA5B8;
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox QAbstractItemView {{
    background: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    selection-background-color: #EAF1FF;
    outline: 0;
}}

QTableWidget {{
    background: {COLOR_CARD};
    border: none;
    gridline-color: transparent;
    selection-background-color: #EAF1FF;
    selection-color: {COLOR_TEXT};
    font-size: 14px;
}}

QTableWidget::item {{
    border-bottom: 1px solid #EEF2F7;
    padding-left: 12px;
    padding-right: 12px;
}}

QTableWidget::item:selected {{
    background: #EAF1FF;
    color: {COLOR_BLUE};
}}

QHeaderView::section {{
    background: {COLOR_CARD};
    color: {COLOR_TEXT};
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    padding-left: 12px;
    padding-right: 12px;
    min-height: 44px;
    font-size: 14px;
    font-weight: 800;
}}

QScrollBar:vertical {{
    width: 10px;
    background: transparent;
}}

QScrollBar::handle:vertical {{
    background: #C9D2E3;
    border-radius: 5px;
    min-height: 34px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


def apply_shadow(widget: QWidget, blur: int = 22, y_offset: int = 5, alpha: int = 28) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y_offset)
    shadow.setColor(QColor(12, 31, 77, alpha))
    widget.setGraphicsEffect(shadow)


def card_stylesheet() -> str:
    return f"""
    QFrame {{
        background: {COLOR_CARD};
        border: 1px solid {COLOR_BORDER};
        border-radius: {CARD_RADIUS}px;
    }}
    """


def button_stylesheet(variant: str) -> str:
    palettes = {
        "primary": (COLOR_BLUE, "#FFFFFF", COLOR_BLUE_HOVER, COLOR_BLUE),
        "secondary": ("#EEF2F8", COLOR_TEXT, "#E3EAF5", "#EEF2F8"),
        "outline": (COLOR_CARD, COLOR_BLUE, "#F2F6FF", COLOR_BLUE),
        "danger": (COLOR_CARD, COLOR_DANGER, "#FFF1F3", COLOR_DANGER),
        "success": (COLOR_SUCCESS, "#FFFFFF", "#12864F", COLOR_SUCCESS),
    }
    bg, fg, hover, border = palettes.get(variant, palettes["primary"])
    return f"""
    QPushButton {{
        min-height: {BUTTON_HEIGHT}px;
        padding: 0 18px;
        border-radius: 8px;
        border: 1px solid {border};
        background: {bg};
        color: {fg};
        font-size: 14px;
        font-weight: 700;
    }}
    QPushButton:hover {{
        background: {hover};
    }}
    QPushButton:pressed {{
        background: {border};
        color: #FFFFFF;
    }}
    """


def sidebar_button_stylesheet(active: bool) -> str:
    if active:
        return f"""
        QPushButton {{
            background: {COLOR_BLUE};
            color: #FFFFFF;
            border: none;
            border-radius: 10px;
            padding: 0 20px;
            text-align: left;
            font-size: 15px;
            font-weight: 700;
            min-height: 70px;
        }}
        QPushButton:hover {{
            background: {COLOR_BLUE_HOVER};
        }}
        """
    return f"""
    QPushButton {{
        background: transparent;
        color: rgba(255, 255, 255, 0.86);
        border: none;
        border-radius: 10px;
        padding: 0 20px;
        text-align: left;
        font-size: 15px;
        font-weight: 600;
        min-height: 64px;
    }}
    QPushButton:hover {{
        background: rgba(255, 255, 255, 0.08);
        color: #FFFFFF;
    }}
    """


def sidebar_stylesheet() -> str:
    return f"""
    QFrame#Sidebar {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_NAVY},
            stop:1 {COLOR_NAVY_DARK}
        );
    }}
    """


def table_card_height(row_count: int) -> int:
    return 54 + max(row_count, 1) * TABLE_ROW_HEIGHT + 18
