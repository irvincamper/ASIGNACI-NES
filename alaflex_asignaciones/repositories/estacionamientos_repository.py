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
