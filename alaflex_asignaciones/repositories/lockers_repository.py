from __future__ import annotations

from database.connection import get_connection


class LockersRepository:
    def count_ocupados(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM lockers WHERE estado = 'Ocupado'").fetchone()
        return int(row["total"])

    def list_all(self) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute("SELECT id, numero, estado, id_empleado FROM lockers ORDER BY numero").fetchall()
        return [dict(row) for row in rows]
