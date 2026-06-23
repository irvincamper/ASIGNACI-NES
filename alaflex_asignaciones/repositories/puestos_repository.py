from __future__ import annotations

from database.connection import get_connection


class PuestosRepository:
    def list_all(self) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, nombre, activo FROM puestos ORDER BY nombre"
            ).fetchall()
        return [dict(row) for row in rows]

    def list_active(self) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, nombre, activo FROM puestos WHERE activo = 1 ORDER BY nombre"
            ).fetchall()
        return [dict(row) for row in rows]
