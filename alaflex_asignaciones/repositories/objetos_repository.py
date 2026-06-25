from __future__ import annotations

from database.connection import get_connection


class ObjetosRepository:
    def list_summary(self, search: str = "", categoria: str = "Todas las categorias", estado: str = "Todos los estados") -> list[dict]:
        filters = []
        params: list[str] = []
        if search:
            filters.append("nombre LIKE ?")
            params.append(f"%{search}%")
        if categoria and not categoria.startswith("Todas las categor"):
            filters.append("categoria = ?")
            params.append(categoria)
        if estado and estado != "Todos los estados":
            filters.append("activo = ?")
            params.append("1" if estado == "Activo" else "0")
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    id,
                    nombre,
                    categoria,
                    CASE requiere_devolucion WHEN 1 THEN 'Sí' ELSE 'No' END AS requiere,
                    CASE activo WHEN 1 THEN 'Activo' ELSE 'Inactivo' END AS estado,
                    COALESCE(observaciones, '') AS observaciones
                FROM objetos
                {where}
                ORDER BY nombre
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def list_categories(self) -> list[str]:
        with get_connection() as connection:
            rows = connection.execute("SELECT DISTINCT categoria FROM objetos ORDER BY categoria").fetchall()
        return [row["categoria"] for row in rows]

    def find_by_name(self, nombre: str, exclude_id: int | None = None) -> dict | None:
        params: list = [nombre.strip().upper()]
        clause = "UPPER(TRIM(nombre)) = ?"
        if exclude_id is not None:
            clause += " AND id != ?"
            params.append(exclude_id)
        with get_connection() as connection:
            row = connection.execute(f"SELECT id, nombre FROM objetos WHERE {clause} LIMIT 1", params).fetchone()
        return dict(row) if row else None

    def kpis(self) -> dict[str, int]:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN requiere_devolucion = 1 THEN 1 ELSE 0 END) AS con_devolucion,
                    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) AS activos
                FROM objetos
                """
            ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "con_devolucion": int(row["con_devolucion"] or 0),
            "activos": int(row["activos"] or 0),
        }

    def create(self, nombre: str, categoria: str, requiere_devolucion: int, activo: int, observaciones: str = "") -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO objetos (nombre, categoria, requiere_devolucion, activo, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre, categoria, requiere_devolucion, activo, observaciones),
            )
            return int(cursor.lastrowid)

    def update(
        self,
        objeto_id: int,
        nombre: str,
        categoria: str,
        requiere_devolucion: int,
        activo: int,
        observaciones: str = "",
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE objetos
                SET nombre = ?,
                    categoria = ?,
                    requiere_devolucion = ?,
                    activo = ?,
                    observaciones = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (nombre, categoria, requiere_devolucion, activo, observaciones, objeto_id),
            )

    def deactivate(self, objeto_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE objetos
                SET activo = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (objeto_id,),
            )
