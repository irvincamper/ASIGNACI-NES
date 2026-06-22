from __future__ import annotations

from PySide6.QtWidgets import QLineEdit

from app.theme import COLOR_TEXT_MUTED
from utils.formatters import icon_from_name


class SearchBar(QLineEdit):
    def __init__(self, placeholder: str, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.addAction(icon_from_name("fa5s.search", COLOR_TEXT_MUTED), QLineEdit.LeadingPosition)
