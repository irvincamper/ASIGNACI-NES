from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.styles import sidebar_button_stylesheet, sidebar_stylesheet
from app.theme import SIDEBAR_WIDTH
from utils.constants import LOGO_PATH, MODULES
from utils.formatters import icon_from_name


class Sidebar(QFrame):
    module_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setStyleSheet(sidebar_stylesheet())
        self.buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 36, 14, 0)
        layout.setSpacing(12)

        logo_block = QWidget()
        logo_block.setFixedHeight(96)
        logo_layout = QHBoxLayout(logo_block)
        logo_layout.setContentsMargins(22, 0, 12, 0)
        logo_layout.setSpacing(12)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(58, 58)
        pixmap = QPixmap(str(LOGO_PATH))
        if pixmap.isNull():
            logo.setText("A")
            logo.setStyleSheet("color: #FFFFFF; font-size: 30px; font-weight: 900;")
        else:
            logo.setPixmap(pixmap.scaled(58, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        text = QLabel("ALAFLEX")
        text.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: 900; letter-spacing: 0px;")
        logo_layout.addWidget(logo)
        logo_layout.addWidget(text, 1)

        layout.addWidget(logo_block)
        layout.addSpacing(18)

        for module in MODULES:
            button = QPushButton(module["title"])
            button.setCursor(Qt.PointingHandCursor)
            button.setIcon(icon_from_name(module["icon"], "#FFFFFF"))
            button.setIconSize(QSize(18, 18))
            button.clicked.connect(lambda _checked=False, key=module["key"]: self.module_selected.emit(key))
            self.buttons[module["key"]] = button
            layout.addWidget(button)

        layout.addStretch(1)
        self.set_active("dashboard")

    def set_active(self, module_key: str) -> None:
        for key, button in self.buttons.items():
            is_active = key == module_key
            button.setStyleSheet(sidebar_button_stylesheet(is_active))
            icon_color = "#FFFFFF" if is_active else "#DCE6F8"
            module = next(item for item in MODULES if item["key"] == key)
            button.setIcon(icon_from_name(module["icon"], icon_color))
