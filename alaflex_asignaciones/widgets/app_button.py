from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QPushButton

from app.styles import button_stylesheet
from app.theme import COLOR_BLUE, COLOR_DANGER, COLOR_SUCCESS, COLOR_TEXT
from utils.formatters import icon_from_name


class AppButton(QPushButton):
    def __init__(
        self,
        text: str,
        icon_name: str | None = None,
        variant: str = "primary",
        parent=None,
    ) -> None:
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(button_stylesheet(variant))

        if icon_name:
            color = {
                "primary": "#FFFFFF",
                "success": "#FFFFFF",
                "danger": COLOR_DANGER,
                "outline": COLOR_BLUE,
                "secondary": COLOR_TEXT,
            }.get(variant, COLOR_SUCCESS)
            self.setIcon(icon_from_name(icon_name, color))
            self.setIconSize(QSize(18, 18))
