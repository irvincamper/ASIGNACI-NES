from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QLineEdit, QVBoxLayout

from app.styles import apply_shadow
from app.theme import COLOR_BG, COLOR_BORDER, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED
from widgets.app_button import AppButton


class FormDialog(QDialog):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setFixedSize(560, 320)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_BG}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 20)
        layout.setSpacing(14)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 21px; font-weight: 800;")

        note = QLabel("Formulario visual preparado para conectarse en Etapa 2.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px;")

        field = QLineEdit()
        field.setPlaceholderText("Campo de ejemplo")

        button = AppButton("Cerrar", "fa5s.check", "primary")
        button.clicked.connect(self.accept)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            f"""
            QFrame#Card {{
                background: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 14px;
            }}
            """
        )
        apply_shadow(card, blur=18, y_offset=4, alpha=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)
        card_layout.addWidget(title_label)
        card_layout.addWidget(note)
        card_layout.addWidget(field)

        layout.addWidget(card)
        layout.addWidget(button)
