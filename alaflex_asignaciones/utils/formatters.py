from __future__ import annotations

import qtawesome as qta
from PySide6.QtGui import QIcon

from app.theme import COLOR_BLUE


def icon_from_name(icon_name: str, color: str = COLOR_BLUE) -> QIcon:
    try:
        return qta.icon(icon_name, color=color)
    except Exception:
        return qta.icon("fa5s.circle", color=color)


def yes_no(value: bool) -> str:
    return "Sí" if value else "No"
