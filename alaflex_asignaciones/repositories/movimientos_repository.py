from __future__ import annotations

import sqlite3

from database.connection import get_connection


class MovimientosRepository:
    def insert(
        self,
        tipo: str,
        descripcion: str,
        id_empleado: int | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        if connection is not None:
            connection.execute(
                "INSERT INTO movimientos (tipo, descripcion, id_empleado) VALUES (?, ?, ?)",
                (tipo, descripcion, id_empleado),
            )
            return
        with get_connection() as local_connection:
            local_connection.execute(
                "INSERT INTO movimientos (tipo, descripcion, id_empleado) VALUES (?, ?, ?)",
                (tipo, descripcion, id_empleado),
            )

    def list_recent(self, limit: int = 20) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, tipo, descripcion, id_empleado, created_at FROM movimientos ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
