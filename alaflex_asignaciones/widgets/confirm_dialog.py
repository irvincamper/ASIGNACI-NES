from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.styles import apply_shadow, button_stylesheet
from app.theme import COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED
from utils.constants import MOCK_ACTION_MESSAGE
from utils.formatters import icon_from_name


class ConfirmDialog(QDialog):
    def __init__(self, title: str, message: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(430)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_CARD}; border-radius: 14px; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setFixedSize(46, 46)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icon_from_name("fa5s.info-circle", COLOR_BLUE).pixmap(24, 24))
        icon.setStyleSheet("QLabel { background: #EAF1FF; border-radius: 23px; }")

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 18px; font-weight: 800;")

        header.addWidget(icon)
        header.addWidget(title_label, 1)

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; line-height: 150%;")

        button = QPushButton("Entendido")
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(button_stylesheet("primary"))
        button.clicked.connect(self.accept)

        layout.addLayout(header)
        layout.addWidget(message_label)
        layout.addWidget(button)

        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QLabel {{
                border: none;
            }}
            QPushButton {{
                border: 1px solid {COLOR_BORDER};
            }}
            """
        )
        apply_shadow(self)

    @staticmethod
    def show_mock(parent=None, title: str = "Etapa 2") -> None:
        dialog = ConfirmDialog(title, MOCK_ACTION_MESSAGE, parent)
        dialog.exec()
