from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from app.styles import apply_shadow, rgba
from app.theme import COLOR_CARD, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_MUTED
from utils.formatters import icon_from_name


class KpiCard(QFrame):
    def __init__(
        self,
        icon_name: str,
        value: str,
        title: str,
        color: str,
        subtitle: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(112)
        self.setStyleSheet(
            f"""
            QFrame#Card {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 16px;
            }}
            """
        )
        apply_shadow(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(24)

        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setPixmap(icon_from_name(icon_name, color).pixmap(30, 30))
        icon_label.setStyleSheet(
            f"""
            QLabel {{
                background: {rgba(color, 0.13)};
                border-radius: 32px;
            }}
            """
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 800;")

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 500;")

        text_layout.addStretch(1)
        text_layout.addWidget(value_label)
        text_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")
            text_layout.addWidget(subtitle_label)

        text_layout.addStretch(1)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
        layout.addStretch(1)
