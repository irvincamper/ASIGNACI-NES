from __future__ import annotations

from database.connection import get_connection


class EmpleadosRepository:
    def list_summary(self, search: str = "", estado: str = "Todos") -> list[dict]:
        filters = []
        params: list[str] = []
        if search:
            filters.append("(e.matricula LIKE ? OR e.nombre LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like])
        if estado and estado not in {"Todos", "Estado: Todos"}:
            filters.append("e.estado = ?")
            params.append(estado)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    e.id,
                    e.matricula,
                    e.nombre,
                    p.nombre AS puesto,
                    e.turno,
                    e.estado,
                    COALESCE((SELECT SUM(cantidad) FROM asignaciones a WHERE a.id_empleado = e.id AND a.estado = 'Asignado'), 0) AS asignados,
                    COALESCE((SELECT SUM(cantidad) FROM asignaciones a WHERE a.id_empleado = e.id AND a.estado = 'Pendiente'), 0) AS pendientes,
                    COALESCE((SELECT SUM(cantidad) FROM asignaciones a WHERE a.id_empleado = e.id AND a.estado = 'Pendiente de devolución'), 0) AS pendientes_de_devolucion,
                    COALESCE((SELECT COUNT(*) FROM asignaciones a WHERE a.id_empleado = e.id), 0) AS total_asignaciones,
                    COALESCE((SELECT cajon FROM estacionamientos es WHERE es.id_empleado = e.id LIMIT 1), '-') AS estacionamiento,
                    COALESCE((SELECT numero FROM lockers l WHERE l.id_empleado = e.id LIMIT 1), '-') AS locker
                FROM empleados e
                JOIN puestos p ON p.id = e.id_puesto
                {where}
                ORDER BY e.matricula
                """,
                params,
            ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            item["objetos"] = f"A: {item['asignados']} / P: {item['pendientes']}"
            output.append(item)
        return output

    def count_activos(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM empleados WHERE estado = 'Activo'").fetchone()
        return int(row["total"])

    def get_first(self) -> dict | None:
        rows = self.list_summary()
        return rows[0] if rows else None

    def get_by_matricula(self, matricula: str) -> dict | None:
        return self.get_profile_by_matricula(matricula)

    def get_profile_by_id(self, empleado_id: int) -> dict | None:
        rows = self._profiles("WHERE e.id = ?", [empleado_id])
        return rows[0] if rows else None

    def get_profile_by_matricula(self, matricula: str) -> dict | None:
        rows = self._profiles("WHERE e.matricula = ?", [matricula])
        return rows[0] if rows else None

    def _profiles(self, where: str = "", params: list | None = None) -> list[dict]:
        params = params or []
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    e.id AS id_empleado,
                    e.id,
                    e.matricula,
                    e.nombre,
                    e.id_puesto,
                    p.nombre AS puesto,
                    e.turno,
                    e.estado,
                    e.fecha_ingreso,
                    COALESCE((SELECT cajon FROM estacionamientos es WHERE es.id_empleado = e.id LIMIT 1), '-') AS estacionamiento,
                    COALESCE((SELECT numero FROM lockers l WHERE l.id_empleado = e.id LIMIT 1), '-') AS locker,
                    COALESCE((SELECT SUM(cantidad) FROM asignaciones a WHERE a.id_empleado = e.id AND a.estado = 'Asignado'), 0) AS asignados,
                    COALESCE((SELECT SUM(cantidad) FROM asignaciones a WHERE a.id_empleado = e.id AND a.estado = 'Pendiente'), 0) AS pendientes,
                    COALESCE((SELECT SUM(cantidad) FROM asignaciones a WHERE a.id_empleado = e.id AND a.estado = 'Pendiente de devolución'), 0) AS pendientes_de_devolucion,
                    COALESCE((SELECT COUNT(*) FROM asignaciones a WHERE a.id_empleado = e.id), 0) AS total_asignaciones
                FROM empleados e
                LEFT JOIN puestos p ON p.id = e.id_puesto
                {where}
                ORDER BY e.matricula
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]
