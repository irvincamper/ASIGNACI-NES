from __future__ import annotations

from database.connection import get_connection


class EstacionamientosRepository:
    def list_summary(self, search: str = "", estado: str = "Todos los estados") -> list[dict]:
        filters = []
        params: list[str] = []
        if search:
            filters.append("(es.cajon LIKE ? OR e.matricula LIKE ? OR e.nombre LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like])
        if estado and estado != "Todos los estados":
            filters.append("es.estado = ?")
            params.append(estado)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    es.cajon,
                    es.estado,
                    es.observaciones,
                    COALESCE(es.updated_at, es.created_at, '-') AS fecha,
                    COALESCE(e.matricula, '-') AS matricula,
                    COALESCE(e.nombre, '-') AS empleado,
                    COALESCE(es.tipo_asignacion, '-') AS tipo
                FROM estacionamientos es
                LEFT JOIN empleados e ON e.id = es.id_empleado
                {where}
                ORDER BY es.cajon
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def count_by_estado(self, estado: str) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM estacionamientos WHERE estado = ?", (estado,)).fetchone()
        return int(row["total"])

    def total(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM estacionamientos").fetchone()
        return int(row["total"])

    def get_by_cajon(self, cajon: str) -> dict | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT es.*, e.matricula, e.nombre AS empleado, e.estado AS empleado_estado
                FROM estacionamientos es
                LEFT JOIN empleados e ON e.id = es.id_empleado
                WHERE es.cajon = ?
                """,
                (cajon,),
            ).fetchone()
        return dict(row) if row else None

    def get_employee_by_matricula(self, matricula: str) -> dict | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, matricula, nombre, estado
                FROM empleados
                WHERE matricula = ?
                """,
                (matricula,),
            ).fetchone()
        return dict(row) if row else None

    def get_employee_parking(self, empleado_id: int) -> dict | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM estacionamientos WHERE id_empleado = ? LIMIT 1",
                (empleado_id,),
            ).fetchone()
        return dict(row) if row else None

    def assign(self, cajon: str, empleado_id: int, tipo_asignacion: str, observaciones: str, replace_existing: bool = False) -> None:
        with get_connection() as connection:
            current = connection.execute("SELECT cajon FROM estacionamientos WHERE id_empleado = ? LIMIT 1", (empleado_id,)).fetchone()
            if current and replace_existing:
                connection.execute(
                    """
                    INSERT INTO historial_estacionamientos
                        (id_empleado, cajon_anterior, cajon_nuevo, fecha_movimiento, tipo_movimiento, observaciones)
                    VALUES (?, ?, ?, DATE('now', 'localtime'), 'Reasignacion', ?)
                    """,
                    (empleado_id, current["cajon"], cajon, observaciones),
                )
                connection.execute(
                    """
                    UPDATE estacionamientos
                    SET estado = 'Libre',
                        id_empleado = NULL,
                        tipo_asignacion = NULL,
                        observaciones = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_empleado = ?
                    """,
                    (empleado_id,),
                )
            connection.execute(
                """
                UPDATE estacionamientos
                SET estado = 'Ocupado',
                    id_empleado = ?,
                    tipo_asignacion = ?,
                    observaciones = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cajon = ?
                """,
                (empleado_id, tipo_asignacion, observaciones, cajon),
            )
            connection.execute(
                """
                INSERT INTO historial_estacionamientos
                    (id_empleado, cajon_anterior, cajon_nuevo, fecha_movimiento, tipo_movimiento, observaciones)
                VALUES (?, ?, ?, DATE('now', 'localtime'), 'Asignacion', ?)
                """,
                (empleado_id, current["cajon"] if current else None, cajon, observaciones),
            )

    def release(self, cajon: str, observaciones: str) -> None:
        with get_connection() as connection:
            current = connection.execute("SELECT id_empleado, cajon FROM estacionamientos WHERE cajon = ?", (cajon,)).fetchone()
            empleado_id = current["id_empleado"] if current else None
            connection.execute(
                """
                INSERT INTO historial_estacionamientos
                    (id_empleado, cajon_anterior, cajon_nuevo, fecha_movimiento, tipo_movimiento, observaciones)
                VALUES (?, ?, NULL, DATE('now', 'localtime'), 'Liberacion', ?)
                """,
                (empleado_id, cajon, observaciones),
            )
            connection.execute(
                """
                UPDATE estacionamientos
                SET estado = 'Libre',
                    id_empleado = NULL,
                    tipo_asignacion = NULL,
                    observaciones = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cajon = ?
                """,
                (observaciones, cajon),
            )
