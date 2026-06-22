from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout

from app.theme import COLOR_CARD, COLOR_TEXT, COLOR_TEXT_MUTED
from widgets.app_button import AppButton


class FormDialog(QDialog):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(520)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_CARD}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
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

        layout.addWidget(title_label)
        layout.addWidget(note)
        layout.addWidget(field)
        layout.addWidget(button)
