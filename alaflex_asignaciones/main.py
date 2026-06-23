from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.styles import GLOBAL_STYLES
from database.connection import init_database


def main() -> int:
    init_database()

    app = QApplication(sys.argv)
    app.setApplicationName("ALAFLEX - Sistema de Asignaciones")
    app.setOrganizationName("ALAFLEX")
    app.setStyleSheet(GLOBAL_STYLES)

    window = MainWindow()
    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
