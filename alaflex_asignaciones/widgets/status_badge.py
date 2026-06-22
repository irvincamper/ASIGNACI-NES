from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from app.theme import CATEGORY_STYLES, STATUS_STYLES


class StatusBadge(QLabel):
    def __init__(self, text: str, badge_type: str = "status", parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(28)
        self.setContentsMargins(10, 0, 10, 0)

        palette = CATEGORY_STYLES if badge_type == "category" else STATUS_STYLES
        foreground, background = palette.get(text, STATUS_STYLES.get(text, ("#687386", "#F1F3F7")))
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {foreground};
                background: {background};
                border: 1px solid {foreground}22;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )
