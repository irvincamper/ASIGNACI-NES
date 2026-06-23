from __future__ import annotations

import sqlite3

from database.connection import get_connection


class AsignacionesRepository:
    DUPLICATE_STATES = ("Pendiente", "Asignado", "Pendiente de devolución", "Devuelto", "No aplica")

    def count_by_estado(self, estado: str) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM asignaciones WHERE estado = ?", (estado,)).fetchone()
        return int(row["total"])

    def count_asignadas(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(cantidad), 0) AS total FROM asignaciones WHERE estado = 'Asignado'"
            ).fetchone()
        return int(row["total"])

    def count_total(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM asignaciones").fetchone()
        return int(row["total"])

    def count_empleados_activos_sin_asignaciones(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM empleados e
                WHERE e.estado = 'Activo'
                  AND NOT EXISTS (SELECT 1 FROM asignaciones a WHERE a.id_empleado = e.id)
                """
            ).fetchone()
        return int(row["total"])

    def list_for_employee(self, empleado_id: int) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    a.id AS id_asignacion,
                    o.nombre AS concepto,
                    o.nombre AS objeto,
                    o.categoria,
                    a.cantidad,
                    a.estado,
                    CASE o.requiere_devolucion WHEN 1 THEN 'Sí' ELSE 'No' END AS requiere_devolucion,
                    a.fecha_asignacion AS fecha,
                    a.observaciones
                FROM asignaciones a
                JOIN objetos o ON o.id = a.id_objeto
                WHERE a.id_empleado = ?
                ORDER BY o.nombre
                """,
                (empleado_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_active_employees_for_generation(self, connection: sqlite3.Connection) -> list[dict]:
        rows = connection.execute(
            """
            SELECT
                e.id,
                e.matricula,
                e.nombre,
                e.id_puesto,
                e.turno,
                e.estado,
                p.nombre AS puesto
            FROM empleados e
            LEFT JOIN puestos p ON p.id = e.id_puesto
            WHERE e.estado = 'Activo'
            ORDER BY e.matricula
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def get_employee_for_generation(self, connection: sqlite3.Connection, empleado_id: int) -> dict | None:
        row = connection.execute(
            """
            SELECT
                e.id,
                e.matricula,
                e.nombre,
                e.id_puesto,
                e.turno,
                e.estado,
                p.nombre AS puesto
            FROM empleados e
            LEFT JOIN puestos p ON p.id = e.id_puesto
            WHERE e.id = ?
            """,
            (empleado_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_active_rules_for_position(self, connection: sqlite3.Connection, puesto_id: int) -> list[dict]:
        rows = connection.execute(
            """
            SELECT
                r.id AS id_regla,
                r.id_objeto,
                r.cantidad,
                r.requiere_devolucion,
                o.nombre AS objeto,
                o.activo AS objeto_activo,
                o.stock_disponible,
                o.categoria
            FROM reglas_por_puesto r
            JOIN objetos o ON o.id = r.id_objeto
            WHERE r.id_puesto = ?
              AND r.activo = 1
            ORDER BY o.nombre
            """,
            (puesto_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def find_existing_assignment(
        self,
        connection: sqlite3.Connection,
        empleado_id: int,
        objeto_id: int,
    ) -> dict | None:
        placeholders = ", ".join("?" for _ in self.DUPLICATE_STATES)
        row = connection.execute(
            f"""
            SELECT id, estado
            FROM asignaciones
            WHERE id_empleado = ?
              AND id_objeto = ?
              AND estado IN ({placeholders})
            LIMIT 1
            """,
            (empleado_id, objeto_id, *self.DUPLICATE_STATES),
        ).fetchone()
        return dict(row) if row else None

    def create_pending_assignment(
        self,
        connection: sqlite3.Connection,
        empleado_id: int,
        objeto_id: int,
        cantidad: int,
        requiere_devolucion: int,
        observaciones: str = "",
    ) -> int:
        cursor = connection.execute(
            """
            INSERT INTO asignaciones
                (id_empleado, id_objeto, cantidad, tipo_movimiento, estado, fecha_asignacion, observaciones)
            VALUES (?, ?, ?, 'Generación de asignaciones pendientes', 'Pendiente', NULL, ?)
            """,
            (empleado_id, objeto_id, cantidad, observaciones),
        )
        return int(cursor.lastrowid)
