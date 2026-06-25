from __future__ import annotations

import json

from database.connection import get_connection


class ExpedientesRepository:
    def count_all(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM expedientes_digitales").fetchone()
        return int(row["total"])

    def insert_generated(self, json_snapshot: dict, ruta_pdf: str) -> int:
        empleado = json_snapshot.get("empleado", {})
        recursos = json_snapshot.get("recursos", [])
        json_text = json.dumps(json_snapshot, ensure_ascii=False, indent=2)
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO expedientes_digitales
                    (
                        id_empleado,
                        matricula,
                        motivo,
                        ruta_pdf,
                        fecha_generacion,
                        total_recursos,
                        paginas,
                        revision,
                        estado,
                        json_snapshot,
                        json_congelado
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Generado', ?, ?)
                """,
                (
                    int(empleado["id_empleado"]),
                    str(empleado["matricula"]),
                    str(json_snapshot.get("motivo", "")),
                    ruta_pdf,
                    str(json_snapshot.get("fecha_generacion", "")),
                    int(json_snapshot.get("total_recursos") or len(recursos)),
                    int(json_snapshot.get("paginas") or 1),
                    str(json_snapshot.get("revision", "2")),
                    json_text,
                    json_text,
                ),
            )
            expediente_id = int(cursor.lastrowid)
            detalle = [
                (
                    expediente_id,
                    str(item.get("objeto") or item.get("concepto") or ""),
                    int(item.get("cantidad") or 1),
                    str(item.get("estado") or ""),
                    str(item.get("observaciones") or ""),
                )
                for item in recursos
            ]
            if detalle:
                connection.executemany(
                    """
                    INSERT INTO expediente_detalle (id_expediente, concepto, cantidad, estado, observaciones)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    detalle,
                )
            return expediente_id

    def list_by_matricula(self, matricula: str) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    fecha_generacion,
                    motivo,
                    total_recursos,
                    ruta_pdf,
                    estado
                FROM expedientes_digitales
                WHERE matricula = ?
                ORDER BY datetime(created_at) DESC, id DESC
                """,
                (matricula,),
            ).fetchall()
        return [dict(row) for row in rows]
