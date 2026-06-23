from __future__ import annotations

from database.connection import get_connection


class ExpedientesRepository:
    def count_all(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM expedientes_digitales").fetchone()
        return int(row["total"])
