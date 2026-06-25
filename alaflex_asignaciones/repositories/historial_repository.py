from __future__ import annotations

from database.connection import get_connection


class HistorialRepository:
    def list_cambios_puesto(self, id_empleado: int) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, puesto_anterior, puesto_nuevo, fecha_cambio, motivo, observaciones
                FROM historial_cambios_puesto
                WHERE id_empleado = ?
                ORDER BY fecha_cambio DESC, id DESC
                """,
                (id_empleado,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_bajas(self, id_empleado: int) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, fecha_baja, motivo_baja, observaciones
                FROM historial_bajas
                WHERE id_empleado = ?
                ORDER BY fecha_baja DESC, id DESC
                """,
                (id_empleado,),
            ).fetchall()
        return [dict(row) for row in rows]
