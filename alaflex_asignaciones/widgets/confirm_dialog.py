from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.styles import apply_shadow, button_stylesheet
from app.theme import COLOR_BG, COLOR_BLUE, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED
from utils.constants import MOCK_ACTION_MESSAGE
from utils.formatters import icon_from_name


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        parent=None,
        *,
        confirm: bool = False,
        accept_text: str = "Entendido",
        cancel_text: str = "Cancelar",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setFixedWidth(500)
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {COLOR_BG};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 20)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            f"""
            QFrame#Card {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 14px;
            }}
            QLabel {{
                border: none;
            }}
            """
        )
        apply_shadow(card, blur=18, y_offset=4, alpha=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 22)
        card_layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(14)
        icon = QLabel()
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(icon_from_name("fa5s.info-circle", COLOR_BLUE).pixmap(22, 22))
        icon.setStyleSheet("QLabel { background: #EAF1FF; border-radius: 21px; }")

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 20px; font-weight: 900;")

        header.addWidget(icon)
        header.addWidget(title_label, 1)

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; line-height: 150%;")

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        buttons.addStretch(1)
        if confirm:
            cancel = QPushButton(cancel_text)
            cancel.setCursor(Qt.PointingHandCursor)
            cancel.setStyleSheet(button_stylesheet("outline"))
            cancel.clicked.connect(self.reject)
            buttons.addWidget(cancel)

        button = QPushButton(accept_text)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(button_stylesheet("primary"))
        button.clicked.connect(self.accept)
        buttons.addWidget(button)

        card_layout.addLayout(header)
        card_layout.addWidget(message_label)
        card_layout.addLayout(buttons)
        layout.addWidget(card)

        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QPushButton {{
                border: 1px solid {COLOR_BORDER};
            }}
            """
        )

    @staticmethod
    def show_mock(parent=None, title: str = "Función pendiente") -> None:
        dialog = ConfirmDialog(title, MOCK_ACTION_MESSAGE, parent)
        dialog.exec()

    @staticmethod
    def show_message(parent, title: str, message: str) -> None:
        dialog = ConfirmDialog(title, message, parent)
        dialog.exec()

    @staticmethod
    def ask(parent, title: str, message: str, accept_text: str = "Continuar") -> bool:
        dialog = ConfirmDialog(title, message, parent, confirm=True, accept_text=accept_text)
        return dialog.exec() == QDialog.Accepted
