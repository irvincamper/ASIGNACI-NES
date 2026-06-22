from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from app.router import Router
from app.theme import MIN_HEIGHT, MIN_WIDTH
from widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ALAFLEX - Sistema de Asignaciones")
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        root = QWidget()
        root.setObjectName("Root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.router = Router(self)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.router.stack, 1)

        self.setCentralWidget(root)

        self.sidebar.module_selected.connect(self.router.navigate)
        self.router.view_changed.connect(self.sidebar.set_active)
        self.router.navigate("dashboard")
