from __future__ import annotations

import sqlite3
from typing import Any

from utils.normalizers import clean_text, make_lookup_key


FALLBACK_MATRICULAS = {"1001", "1002", "1003", "1004"}


class ImportacionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self._load_caches()

    def _load_caches(self) -> None:
        self.puestos = self._cache_table("puestos", "nombre")
        self.objetos = self._cache_table("objetos", "nombre")
        self.empleados = self._cache_table("empleados", "matricula")
        self.estacionamientos = self._cache_table("estacionamientos", "cajon")
        self.lockers = self._cache_table("lockers", "numero")

    def _cache_table(self, table: str, key_field: str) -> dict[str, dict[str, Any]]:
        rows = self.connection.execute(f"SELECT * FROM {table}").fetchall()
        return {make_lookup_key(row[key_field]): dict(row) for row in rows}

    def has_known_fallback_seed_only(self) -> bool:
        rows = self.connection.execute("SELECT matricula FROM empleados ORDER BY matricula").fetchall()
        matriculas = {row["matricula"] for row in rows}
        if matriculas != FALLBACK_MATRICULAS:
            return False
        expected_counts = {
            "puestos": 5,
            "objetos": 8,
            "empleados": 4,
            "estacionamientos": 5,
            "lockers": 4,
            "reglas_por_puesto": 9,
        }
        for table, expected in expected_counts.items():
            row = self.connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
            if int(row["total"]) != expected:
                return False
        return True

    def clear_importable_data(self) -> None:
        tables = [
            "expediente_detalle",
            "expedientes_digitales",
            "historial_cambios_puesto",
            "historial_bajas",
            "historial_estacionamientos",
            "movimientos",
            "asignaciones",
            "reglas_por_puesto",
            "estacionamientos",
            "lockers",
            "empleados",
            "objetos",
            "puestos",
        ]
        for table in tables:
            self.connection.execute(f"DELETE FROM {table}")
        placeholders = ", ".join("?" for _ in tables)
        self.connection.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})", tables)
        self._load_caches()

    def core_counts(self) -> dict[str, int]:
        tables = ["puestos", "empleados", "objetos", "reglas_por_puesto", "estacionamientos", "lockers"]
        counts: dict[str, int] = {}
        for table in tables:
            row = self.connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
            counts[table] = int(row["total"] or 0)
        return counts

    def get_empleado_id(self, matricula: str) -> int | None:
        row = self.empleados.get(make_lookup_key(matricula))
        return int(row["id"]) if row else None

    def upsert_puesto(self, nombre: str, clave: str = "") -> tuple[int, str]:
        nombre = clean_text(nombre)
        clave = clean_text(clave, uppercase=True)
        key = make_lookup_key(nombre)
        existing = self.puestos.get(key)
        if existing:
            updates: list[str] = []
            params: list[Any] = []
            if clave and not clean_text(existing.get("clave", "")):
                updates.append("clave = ?")
                params.append(clave)
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(existing["id"])
                self.connection.execute(f"UPDATE puestos SET {', '.join(updates)} WHERE id = ?", params)
                existing["clave"] = clave or existing.get("clave")
                return int(existing["id"]), "updated"
            return int(existing["id"]), "unchanged"

        cursor = self.connection.execute(
            "INSERT INTO puestos (nombre, clave, activo) VALUES (?, ?, 1)",
            (nombre, clave or None),
        )
        puesto_id = int(cursor.lastrowid)
        self.puestos[key] = {"id": puesto_id, "nombre": nombre, "clave": clave}
        return puesto_id, "created"

    def upsert_objeto(
        self,
        nombre: str,
        categoria: str,
        stock_total: int = 0,
        stock_disponible: int = 0,
        requiere_devolucion: int = 1,
    ) -> tuple[int, str]:
        nombre = clean_text(nombre)
        categoria = clean_text(categoria) or "Otro"
        stock_total = max(int(stock_total or 0), 0)
        stock_disponible = max(min(int(stock_disponible or 0), stock_total), 0)
        requiere_devolucion = 1 if requiere_devolucion else 0
        key = make_lookup_key(nombre)
        existing = self.objetos.get(key)
        if existing:
            updates: list[str] = []
            params: list[Any] = []
            existing_category = clean_text(existing.get("categoria", ""))
            if categoria and (not existing_category or make_lookup_key(existing_category) == "OTRO"):
                updates.append("categoria = ?")
                params.append(categoria)
                existing["categoria"] = categoria
            if int(existing.get("stock_total") or 0) == 0 and stock_total > 0:
                updates.extend(["stock_total = ?", "stock_disponible = ?"])
                params.extend([stock_total, stock_disponible])
                existing["stock_total"] = stock_total
                existing["stock_disponible"] = stock_disponible
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(existing["id"])
                self.connection.execute(f"UPDATE objetos SET {', '.join(updates)} WHERE id = ?", params)
                return int(existing["id"]), "updated"
            return int(existing["id"]), "unchanged"

        cursor = self.connection.execute(
            """
            INSERT INTO objetos
                (nombre, categoria, stock_total, stock_disponible, requiere_devolucion, activo)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (nombre, categoria, stock_total, stock_disponible, requiere_devolucion),
        )
        objeto_id = int(cursor.lastrowid)
        self.objetos[key] = {
            "id": objeto_id,
            "nombre": nombre,
            "categoria": categoria,
            "stock_total": stock_total,
            "stock_disponible": stock_disponible,
            "requiere_devolucion": requiere_devolucion,
        }
        return objeto_id, "created"

    def upsert_empleado(
        self,
        matricula: str,
        nombre: str,
        puesto_id: int,
        turno: str,
        fecha_ingreso: str = "Pendiente",
    ) -> tuple[int, str]:
        matricula = clean_text(matricula)
        nombre = clean_text(nombre)
        turno = clean_text(turno) or "Pendiente de revisión"
        fecha_ingreso = clean_text(fecha_ingreso) or "Pendiente"
        key = make_lookup_key(matricula)
        existing = self.empleados.get(key)
        if existing:
            updates: list[str] = []
            params: list[Any] = []
            existing_name = clean_text(existing.get("nombre", ""))
            if nombre and (not existing_name or len(nombre) > len(existing_name)):
                updates.append("nombre = ?")
                params.append(nombre)
                existing["nombre"] = nombre
            existing_turno = make_lookup_key(existing.get("turno", ""))
            if turno and existing_turno in {"", "PENDIENTE DE REVISION"}:
                updates.append("turno = ?")
                params.append(turno)
                existing["turno"] = turno
            existing_fecha = make_lookup_key(existing.get("fecha_ingreso", ""))
            new_fecha = make_lookup_key(fecha_ingreso)
            if fecha_ingreso and existing_fecha in {"", "PENDIENTE"} and new_fecha != existing_fecha:
                updates.append("fecha_ingreso = ?")
                params.append(fecha_ingreso)
                existing["fecha_ingreso"] = fecha_ingreso
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(existing["id"])
                self.connection.execute(f"UPDATE empleados SET {', '.join(updates)} WHERE id = ?", params)
                return int(existing["id"]), "updated"
            return int(existing["id"]), "unchanged"

        cursor = self.connection.execute(
            """
            INSERT INTO empleados
                (matricula, nombre, id_puesto, turno, fecha_ingreso, estado, observaciones)
            VALUES (?, ?, ?, ?, ?, 'Activo', ?)
            """,
            (matricula, nombre, puesto_id, turno, fecha_ingreso, "Importado desde carpeta IMPORTAR"),
        )
        empleado_id = int(cursor.lastrowid)
        self.empleados[key] = {
            "id": empleado_id,
            "matricula": matricula,
            "nombre": nombre,
            "id_puesto": puesto_id,
            "turno": turno,
            "fecha_ingreso": fecha_ingreso,
        }
        return empleado_id, "created"

    def upsert_regla(
        self,
        puesto_id: int,
        objeto_id: int,
        cantidad: int,
        obligatorio: int,
        requiere_devolucion: int,
    ) -> str:
        row = self.connection.execute(
            """
            SELECT id, cantidad, obligatorio, requiere_devolucion, activo
            FROM reglas_por_puesto
            WHERE id_puesto = ? AND id_objeto = ?
            """,
            (puesto_id, objeto_id),
        ).fetchone()
        if row:
            if (
                int(row["cantidad"]) != cantidad
                or int(row["obligatorio"]) != obligatorio
                or int(row["requiere_devolucion"]) != requiere_devolucion
                or int(row["activo"]) != 1
            ):
                self.connection.execute(
                    """
                    UPDATE reglas_por_puesto
                    SET cantidad = ?, obligatorio = ?, requiere_devolucion = ?, activo = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (cantidad, obligatorio, requiere_devolucion, row["id"]),
                )
                return "updated"
            return "unchanged"
        self.connection.execute(
            """
            INSERT INTO reglas_por_puesto
                (id_puesto, id_objeto, cantidad, obligatorio, requiere_devolucion, activo)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (puesto_id, objeto_id, cantidad, obligatorio, requiere_devolucion),
        )
        return "created"

    def upsert_estacionamiento(
        self,
        cajon: str,
        estado: str,
        empleado_id: int | None,
        ubicacion: str = "",
        tipo_asignacion: str = "Importación inicial",
    ) -> tuple[int, str]:
        cajon = clean_text(cajon)
        ubicacion = clean_text(ubicacion)
        key = make_lookup_key(cajon)
        existing = self.estacionamientos.get(key)
        if existing:
            new_values = {
                "estado": estado,
                "id_empleado": empleado_id,
                "tipo_asignacion": tipo_asignacion,
                "ubicacion": ubicacion or None,
            }
            changed = any((existing.get(key_name) or None) != value for key_name, value in new_values.items())
            if changed:
                self.connection.execute(
                    """
                    UPDATE estacionamientos
                    SET estado = ?, id_empleado = ?, tipo_asignacion = ?, ubicacion = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (estado, empleado_id, tipo_asignacion, ubicacion or None, existing["id"]),
                )
                existing.update(new_values)
                return int(existing["id"]), "updated"
            return int(existing["id"]), "unchanged"
        cursor = self.connection.execute(
            """
            INSERT INTO estacionamientos
                (cajon, estado, id_empleado, tipo_asignacion, ubicacion, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (cajon, estado, empleado_id, tipo_asignacion, ubicacion or None, "Importado desde carpeta IMPORTAR"),
        )
        estacionamiento_id = int(cursor.lastrowid)
        self.estacionamientos[key] = {"id": estacionamiento_id, "cajon": cajon, "estado": estado}
        return estacionamiento_id, "created"

    def upsert_locker(
        self,
        numero: str,
        estado: str,
        empleado_id: int | None,
        ubicacion: str = "",
    ) -> tuple[int, str]:
        numero = clean_text(numero)
        ubicacion = clean_text(ubicacion)
        key = make_lookup_key(numero)
        existing = self.lockers.get(key)
        if existing:
            new_values = {"estado": estado, "id_empleado": empleado_id, "ubicacion": ubicacion or None}
            changed = any((existing.get(key_name) or None) != value for key_name, value in new_values.items())
            if changed:
                self.connection.execute(
                    """
                    UPDATE lockers
                    SET estado = ?, id_empleado = ?, ubicacion = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (estado, empleado_id, ubicacion or None, existing["id"]),
                )
                existing.update(new_values)
                return int(existing["id"]), "updated"
            return int(existing["id"]), "unchanged"
        cursor = self.connection.execute(
            """
            INSERT INTO lockers (numero, estado, id_empleado, ubicacion, observaciones)
            VALUES (?, ?, ?, ?, ?)
            """,
            (numero, estado, empleado_id, ubicacion or None, "Importado desde carpeta IMPORTAR"),
        )
        locker_id = int(cursor.lastrowid)
        self.lockers[key] = {"id": locker_id, "numero": numero, "estado": estado}
        return locker_id, "created"
