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
        *,
        id_objeto: int | None = None,
        id_asignacion: int | None = None,
        estado_anterior: str | None = None,
        estado_nuevo: str | None = None,
        observacion: str | None = None,
    ) -> None:
        if connection is not None:
            self._insert_with_connection(
                connection,
                tipo,
                descripcion,
                id_empleado,
                id_objeto=id_objeto,
                id_asignacion=id_asignacion,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo,
                observacion=observacion,
            )
            return
        with get_connection() as local_connection:
            self._insert_with_connection(
                local_connection,
                tipo,
                descripcion,
                id_empleado,
                id_objeto=id_objeto,
                id_asignacion=id_asignacion,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo,
                observacion=observacion,
            )

    def list_recent(self, limit: int = 20) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, tipo, descripcion, id_empleado, created_at FROM movimientos ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _insert_with_connection(
        self,
        connection: sqlite3.Connection,
        tipo: str,
        descripcion: str,
        id_empleado: int | None,
        *,
        id_objeto: int | None,
        id_asignacion: int | None,
        estado_anterior: str | None,
        estado_nuevo: str | None,
        observacion: str | None,
    ) -> None:
        available = {row["name"] for row in connection.execute("PRAGMA table_info(movimientos)").fetchall()}
        columns = ["tipo", "descripcion", "id_empleado"]
        values = [tipo, descripcion, id_empleado]
        optional_values = {
            "id_objeto": id_objeto,
            "id_asignacion": id_asignacion,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "observacion": observacion,
        }
        for column, value in optional_values.items():
            if column in available:
                columns.append(column)
                values.append(value)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO movimientos ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )
