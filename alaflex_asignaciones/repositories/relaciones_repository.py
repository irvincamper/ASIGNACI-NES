from __future__ import annotations

from database.connection import get_connection


class RelacionesRepository:
    def list_by_puesto(self, puesto_id: int | None = None) -> list[dict]:
        params: list[int] = []
        where = ""
        if puesto_id is not None:
            where = "WHERE r.id_puesto = ?"
            params.append(puesto_id)
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    r.id,
                    r.id_puesto,
                    r.id_objeto,
                    p.nombre AS puesto,
                    o.nombre AS objeto,
                    r.cantidad,
                    CASE r.obligatorio WHEN 1 THEN 'Sí' ELSE 'No' END AS obligatorio,
                    CASE r.requiere_devolucion WHEN 1 THEN 'Sí' ELSE 'No' END AS devolucion,
                    CASE r.activo WHEN 1 THEN 'Activo' ELSE 'Inactivo' END AS estado
                FROM reglas_por_puesto r
                JOIN puestos p ON p.id = r.id_puesto
                JOIN objetos o ON o.id = r.id_objeto
                {where}
                ORDER BY p.nombre, o.nombre
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def list_active_objects(self) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, nombre, requiere_devolucion
                FROM objetos
                WHERE activo = 1
                ORDER BY nombre
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_existing(self, puesto_id: int, objeto_id: int) -> dict | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, activo
                FROM reglas_por_puesto
                WHERE id_puesto = ? AND id_objeto = ?
                """,
                (puesto_id, objeto_id),
            ).fetchone()
        return dict(row) if row else None

    def upsert(self, data: dict, relation_id: int | None = None) -> int:
        with get_connection() as connection:
            if relation_id:
                connection.execute(
                    """
                    UPDATE reglas_por_puesto
                    SET id_objeto = ?,
                        cantidad = ?,
                        obligatorio = ?,
                        requiere_devolucion = ?,
                        activo = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        data["id_objeto"],
                        data["cantidad"],
                        data["obligatorio"],
                        data["requiere_devolucion"],
                        data["activo"],
                        relation_id,
                    ),
                )
                return relation_id
            existing = self.get_existing(int(data["id_puesto"]), int(data["id_objeto"]))
            if existing:
                connection.execute(
                    """
                    UPDATE reglas_por_puesto
                    SET cantidad = ?,
                        obligatorio = ?,
                        requiere_devolucion = ?,
                        activo = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        data["cantidad"],
                        data["obligatorio"],
                        data["requiere_devolucion"],
                        data["activo"],
                        existing["id"],
                    ),
                )
                return int(existing["id"])
            cursor = connection.execute(
                """
                INSERT INTO reglas_por_puesto
                    (id_puesto, id_objeto, cantidad, obligatorio, requiere_devolucion, activo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id_puesto"],
                    data["id_objeto"],
                    data["cantidad"],
                    data["obligatorio"],
                    data["requiere_devolucion"],
                    data["activo"],
                ),
            )
            return int(cursor.lastrowid)

    def deactivate(self, relation_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE reglas_por_puesto
                SET activo = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (relation_id,),
            )

    def kpis(self) -> dict[str, int]:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN obligatorio = 1 THEN 1 ELSE 0 END) AS obligatorias,
                    SUM(CASE WHEN requiere_devolucion = 1 THEN 1 ELSE 0 END) AS con_devolucion
                FROM reglas_por_puesto
                WHERE activo = 1
                """
            ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "obligatorias": int(row["obligatorias"] or 0),
            "con_devolucion": int(row["con_devolucion"] or 0),
        }

    def count_puestos_sin_reglas(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM puestos p
                WHERE p.activo = 1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM reglas_por_puesto r
                      WHERE r.id_puesto = p.id
                        AND r.activo = 1
                  )
                """
            ).fetchone()
        return int(row["total"] or 0)

    def count_objetos_inactivos_en_reglas(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(DISTINCT r.id_objeto) AS total
                FROM reglas_por_puesto r
                JOIN objetos o ON o.id = r.id_objeto
                WHERE r.activo = 1
                  AND o.activo = 0
                """
            ).fetchone()
        return int(row["total"] or 0)
