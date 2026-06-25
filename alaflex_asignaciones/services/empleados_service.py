from __future__ import annotations

from database.connection import get_connection
from repositories.asignaciones_repository import AsignacionesRepository
from repositories.empleados_repository import EmpleadosRepository
from repositories.movimientos_repository import MovimientosRepository
from repositories.puestos_repository import PuestosRepository
from utils.normalizers import normalize_matricula


class EmpleadosService:
    def __init__(self) -> None:
        self.repository = EmpleadosRepository()
        self.asignaciones = AsignacionesRepository()
        self.puestos = PuestosRepository()
        self.movimientos = MovimientosRepository()

    def list_empleados(self, search: str = "", estado: str = "Estado: Todos") -> list[dict]:
        normalized = "Todos" if estado == "Estado: Todos" else estado
        if normalized == "Baja":
            normalized = "Inactivo"
        return self.repository.list_summary(search=search.strip(), estado=normalized)

    def list_puestos(self) -> list[dict]:
        return self.puestos.list_active()

    def list_estacionamientos(self) -> list[str]:
        with get_connection() as connection:
            rows = connection.execute("SELECT cajon FROM estacionamientos ORDER BY cajon").fetchall()
        return [str(row["cajon"]) for row in rows]

    def list_lockers(self) -> list[str]:
        with get_connection() as connection:
            rows = connection.execute("SELECT numero FROM lockers ORDER BY numero").fetchall()
        return [str(row["numero"]) for row in rows]

    def get_first_employee(self) -> dict | None:
        return self.repository.get_first()

    def buscar_por_matricula(self, matricula: str) -> dict | None:
        matricula = normalize_matricula(matricula)
        if not matricula:
            return None
        empleado = self.repository.get_profile_by_matricula(matricula)
        if not empleado:
            return None
        asignaciones = self.asignaciones.list_for_employee(int(empleado["id_empleado"]))
        empleado["asignaciones"] = asignaciones
        empleado["total_asignaciones"] = self.asignaciones.count_objects_for_employee(int(empleado["id_empleado"]))
        empleado["objetos"] = str(empleado["total_asignaciones"])
        return empleado

    def crear_empleado(self, data: dict) -> dict:
        required = ("matricula", "nombre", "id_puesto", "turno", "fecha_ingreso")
        if any(not str(data.get(key, "")).strip() for key in required):
            return {"ok": False, "mensaje": "Completa los campos obligatorios antes de guardar."}
        matricula = normalize_matricula(str(data.get("matricula", "")))
        if self.repository.get_profile_by_matricula(matricula):
            return {"ok": False, "mensaje": "Ya existe un empleado registrado con esa matricula."}

        with get_connection() as connection:
            try:
                estacionamiento = str(data.get("estacionamiento", "")).strip()
                locker = str(data.get("locker", "")).strip()
                ocupado = self._recurso_ocupado(connection, "estacionamientos", "cajon", estacionamiento)
                if ocupado:
                    return {"ok": False, "mensaje": "El estacionamiento seleccionado ya esta ocupado."}
                ocupado = self._recurso_ocupado(connection, "lockers", "numero", locker)
                if ocupado:
                    return {"ok": False, "mensaje": "El locker seleccionado ya esta ocupado."}

                cursor = connection.execute(
                    """
                    INSERT INTO empleados (matricula, nombre, id_puesto, turno, fecha_ingreso, estado, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        matricula,
                        str(data.get("nombre", "")).strip().upper(),
                        int(data["id_puesto"]),
                        str(data.get("turno", "")).strip(),
                        str(data.get("fecha_ingreso", "")).strip(),
                        str(data.get("estado") or "Activo"),
                        str(data.get("observaciones", "")).strip(),
                    ),
                )
                empleado_id = int(cursor.lastrowid)
                self._asignar_estacionamiento(connection, empleado_id, estacionamiento)
                self._asignar_locker(connection, empleado_id, locker)
                creadas = self._generar_objetos_por_puesto(connection, empleado_id, int(data["id_puesto"]))
                self.movimientos.insert(
                    "Alta de empleado",
                    f"Alta de empleado {matricula}; objetos asignados: {creadas}.",
                    empleado_id,
                    connection,
                    observacion=str(data.get("observaciones", "")).strip(),
                )
                connection.commit()
                return {"ok": True, "mensaje": "Empleado creado correctamente.", "id_empleado": empleado_id}
            except Exception as exc:  # noqa: BLE001
                connection.rollback()
                return {"ok": False, "mensaje": f"No fue posible crear el empleado: {exc}"}

    def editar_empleado(self, id_empleado: int, data: dict) -> dict:
        actual = self.repository.get_profile_by_id(id_empleado)
        if not actual:
            return {"ok": False, "mensaje": "No se encontro el empleado seleccionado."}
        required = ("nombre", "id_puesto", "turno", "estado")
        if any(not str(data.get(key, "")).strip() for key in required):
            return {"ok": False, "mensaje": "Completa los campos obligatorios antes de guardar."}

        puesto_anterior_id = int(actual["id_puesto"])
        puesto_nuevo_id = int(data["id_puesto"])
        with get_connection() as connection:
            try:
                estacionamiento = str(data.get("estacionamiento", "")).strip()
                locker = str(data.get("locker", "")).strip()
                ocupado = self._recurso_ocupado(connection, "estacionamientos", "cajon", estacionamiento, id_empleado)
                if ocupado:
                    return {"ok": False, "mensaje": "El estacionamiento seleccionado ya esta ocupado."}
                ocupado = self._recurso_ocupado(connection, "lockers", "numero", locker, id_empleado)
                if ocupado:
                    return {"ok": False, "mensaje": "El locker seleccionado ya esta ocupado."}

                connection.execute(
                    """
                    UPDATE empleados
                    SET nombre = ?, id_puesto = ?, turno = ?, estado = ?, observaciones = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        str(data.get("nombre", "")).strip().upper(),
                        puesto_nuevo_id,
                        str(data.get("turno", "")).strip(),
                        str(data.get("estado") or "Activo"),
                        str(data.get("observaciones", "")).strip(),
                        id_empleado,
                    ),
                )
                self._asignar_estacionamiento(connection, id_empleado, estacionamiento)
                self._asignar_locker(connection, id_empleado, locker)
                if puesto_anterior_id != puesto_nuevo_id:
                    self._sincronizar_objetos_por_puesto(connection, id_empleado, puesto_nuevo_id)
                    puesto_anterior = str(actual.get("puesto", ""))
                    puesto_nuevo = self._puesto_nombre(connection, puesto_nuevo_id)
                    connection.execute(
                        """
                        INSERT INTO historial_cambios_puesto
                            (id_empleado, puesto_anterior, puesto_nuevo, fecha_cambio, motivo, observaciones)
                        VALUES (?, ?, ?, DATE('now', 'localtime'), 'Cambio de puesto', ?)
                        """,
                        (id_empleado, puesto_anterior, puesto_nuevo, str(data.get("observaciones", "")).strip()),
                    )
                    self.movimientos.insert(
                        "Cambio de puesto",
                        f"Cambio de puesto de {puesto_anterior} a {puesto_nuevo}.",
                        id_empleado,
                        connection,
                        observacion=str(data.get("observaciones", "")).strip(),
                    )
                else:
                    self.movimientos.insert("Edicion de empleado", "Datos de empleado actualizados.", id_empleado, connection)
                connection.commit()
                return {"ok": True, "mensaje": "Empleado actualizado correctamente."}
            except Exception as exc:  # noqa: BLE001
                connection.rollback()
                return {"ok": False, "mensaje": f"No fue posible actualizar el empleado: {exc}"}

    def previsualizar_cambio_puesto(self, id_empleado: int, id_puesto_nuevo: int) -> dict:
        actual = self.repository.get_profile_by_id(id_empleado)
        if not actual:
            return {"ok": False, "mensaje": "No se encontro el empleado seleccionado."}
        with get_connection() as connection:
            actuales = self._objetos_actuales(connection, id_empleado)
            nuevas_reglas = self.asignaciones.list_active_rules_for_position(connection, id_puesto_nuevo)
            actual_ids = {int(item["id_objeto"]): item for item in actuales}
            nuevo_ids = {int(item["id_objeto"]): item for item in nuevas_reglas}
            conserva = [actual_ids[obj]["objeto"] for obj in actual_ids.keys() & nuevo_ids.keys()]
            nuevos = [nuevo_ids[obj]["objeto"] for obj in nuevo_ids.keys() - actual_ids.keys()]
            salen = [actual_ids[obj]["objeto"] for obj in actual_ids.keys() - nuevo_ids.keys()]
            return {
                "ok": True,
                "empleado": actual,
                "puesto_anterior": actual.get("puesto", ""),
                "puesto_nuevo": self._puesto_nombre(connection, id_puesto_nuevo),
                "conserva": conserva,
                "nuevos": nuevos,
                "salen": salen,
            }

    def dar_de_baja(self, id_empleado: int, fecha_baja: str, observaciones: str) -> dict:
        if not fecha_baja.strip() or not observaciones.strip():
            return {"ok": False, "mensaje": "Completa los campos obligatorios antes de guardar."}
        empleado = self.repository.get_profile_by_id(id_empleado)
        if not empleado:
            return {"ok": False, "mensaje": "No se encontro el empleado seleccionado."}
        if empleado.get("estado") != "Activo":
            return {"ok": False, "mensaje": "El empleado seleccionado ya se encuentra dado de baja."}
        with get_connection() as connection:
            try:
                connection.execute(
                    """
                    UPDATE empleados
                    SET estado = 'Inactivo', fecha_baja = ?, observaciones = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (fecha_baja.strip(), observaciones.strip(), id_empleado),
                )
                self._liberar_estacionamiento(connection, id_empleado, observaciones)
                self._liberar_locker(connection, id_empleado, observaciones)
                connection.execute(
                    """
                    INSERT INTO historial_bajas (id_empleado, fecha_baja, motivo_baja, observaciones)
                    VALUES (?, ?, ?, ?)
                    """,
                    (id_empleado, fecha_baja.strip(), observaciones.strip(), observaciones.strip()),
                )
                self.movimientos.insert("Baja de empleado", "Empleado dado de baja formalmente.", id_empleado, connection, observacion=observaciones.strip())
                connection.commit()
                return {"ok": True, "mensaje": "Empleado dado de baja correctamente."}
            except Exception as exc:  # noqa: BLE001
                connection.rollback()
                return {"ok": False, "mensaje": f"No fue posible dar de baja al empleado: {exc}"}

    def _generar_objetos_por_puesto(self, connection, id_empleado: int, id_puesto: int) -> int:
        creadas = 0
        for regla in self.asignaciones.list_active_rules_for_position(connection, id_puesto):
            if int(regla.get("objeto_activo") or 0) != 1:
                continue
            if self.asignaciones.find_existing_assignment(connection, id_empleado, int(regla["id_objeto"])):
                continue
            self.asignaciones.create_assigned_assignment(
                connection,
                id_empleado,
                int(regla["id_objeto"]),
                max(int(regla.get("cantidad") or 1), 1),
                "Asignacion registrada automaticamente",
            )
            creadas += 1
        return creadas

    def _sincronizar_objetos_por_puesto(self, connection, id_empleado: int, id_puesto: int) -> None:
        reglas = self.asignaciones.list_active_rules_for_position(connection, id_puesto)
        object_ids = [int(regla["id_objeto"]) for regla in reglas if int(regla.get("objeto_activo") or 0) == 1]
        self.asignaciones.mark_assignments_not_in_objects(
            connection,
            id_empleado,
            object_ids,
            "Objeto conservado como historico por cambio de puesto",
        )
        self._generar_objetos_por_puesto(connection, id_empleado, id_puesto)

    def _objetos_actuales(self, connection, id_empleado: int) -> list[dict]:
        rows = connection.execute(
            """
            SELECT a.id_objeto, o.nombre AS objeto
            FROM asignaciones a
            JOIN objetos o ON o.id = a.id_objeto
            WHERE a.id_empleado = ?
              AND a.estado != 'No aplica'
            """,
            (id_empleado,),
        ).fetchall()
        return [dict(row) for row in rows]

    def _puesto_nombre(self, connection, puesto_id: int) -> str:
        row = connection.execute("SELECT nombre FROM puestos WHERE id = ?", (puesto_id,)).fetchone()
        return str(row["nombre"]) if row else ""

    def _recurso_ocupado(self, connection, table: str, column: str, value: str, empleado_id: int | None = None) -> bool:
        if not value or value == "-":
            return False
        row = connection.execute(
            f"SELECT id_empleado FROM {table} WHERE {column} = ? AND estado = 'Ocupado'",
            (value,),
        ).fetchone()
        return bool(row and row["id_empleado"] not in {None, empleado_id})

    def _asignar_estacionamiento(self, connection, empleado_id: int, cajon: str) -> None:
        self._liberar_estacionamiento(connection, empleado_id, "")
        if cajon and cajon != "-":
            connection.execute(
                """
                UPDATE estacionamientos
                SET estado = 'Ocupado', id_empleado = ?, tipo_asignacion = 'Empleado', updated_at = CURRENT_TIMESTAMP
                WHERE cajon = ?
                """,
                (empleado_id, cajon),
            )

    def _asignar_locker(self, connection, empleado_id: int, numero: str) -> None:
        self._liberar_locker(connection, empleado_id, "")
        if numero and numero != "-":
            connection.execute(
                """
                UPDATE lockers
                SET estado = 'Ocupado', id_empleado = ?, updated_at = CURRENT_TIMESTAMP
                WHERE numero = ?
                """,
                (empleado_id, numero),
            )

    def _liberar_estacionamiento(self, connection, empleado_id: int, observaciones: str) -> None:
        rows = connection.execute("SELECT cajon FROM estacionamientos WHERE id_empleado = ?", (empleado_id,)).fetchall()
        for row in rows:
            connection.execute(
                """
                INSERT INTO historial_estacionamientos
                    (id_empleado, cajon_anterior, cajon_nuevo, fecha_movimiento, tipo_movimiento, observaciones)
                VALUES (?, ?, NULL, DATE('now', 'localtime'), 'Liberacion', ?)
                """,
                (empleado_id, row["cajon"], observaciones),
            )
        connection.execute(
            """
            UPDATE estacionamientos
            SET estado = 'Libre', id_empleado = NULL, tipo_asignacion = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id_empleado = ?
            """,
            (empleado_id,),
        )

    def _liberar_locker(self, connection, empleado_id: int, _observaciones: str) -> None:
        connection.execute(
            """
            UPDATE lockers
            SET estado = 'Libre', id_empleado = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id_empleado = ?
            """,
            (empleado_id,),
        )
