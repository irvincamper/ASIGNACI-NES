from __future__ import annotations

from pathlib import Path

from utils.constants import FUTURE_DATABASE_PATH


def get_future_database_path() -> Path:
    """Return the prepared Etapa 2 SQLite path without opening a connection."""
    return FUTURE_DATABASE_PATH
