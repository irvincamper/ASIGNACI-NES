from __future__ import annotations

from database.connection import get_connection
from repositories.asignaciones_repository import AsignacionesRepository
from repositories.movimientos_repository import MovimientosRepository
from utils.asignaciones_diagnostics import save_asignaciones_diagnostic


class AsignacionesService:
    ESTADOS_VALIDOS = {"Pendiente", "Asignado", "No aplica", "Pendiente de devolución", "Devuelto"}

    def __init__(self) -> None:
        self.repository = AsignacionesRepository()
        self.movimientos = MovimientosRepository()

    def list_for_employee(self, empleado_id: int) -> list[dict]:
        return self.repository.list_for_employee(empleado_id)

    def listar_asignaciones_por_empleado(self, id_empleado: int) -> list[dict]:
        return [
            {
                "objeto": item.get("objeto") or item.get("concepto") or "",
                "categoria": item.get("categoria") or "",
                "cantidad": item.get("cantidad") or "",
                "requiere_devolucion": item.get("requiere_devolucion") or "No",
                "observaciones": item.get("observaciones") or "",
            }
            for item in self.list_for_employee(id_empleado)
        ]

    def contar_objetos_por_empleado(self, id_empleado: int) -> int:
        return self.repository.count_objects_for_employee(id_empleado)

    def resumen_asignaciones_por_empleado(self, id_empleado: int) -> dict[str, int]:
        return self.repository.resumen_por_empleado(id_empleado)

    def cambiar_estado_asignacion(
        self,
        id_asignacion: int,
        nuevo_estado: str,
        observacion: str | None = None,
    ) -> dict:
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            return {"ok": False, "mensaje": "Estado de asignación no válido."}

        with get_connection() as connection:
            try:
                asignacion = self.repository.get_by_id(connection, id_asignacion)
                if not asignacion:
                    return {"ok": False, "mensaje": "No se encontró la asignación seleccionada."}
                estado_anterior = asignacion["estado"]
                error = self._validar_transicion(asignacion, nuevo_estado)
                if error:
                    return {"ok": False, "mensaje": error}
                self.repository.update_assignment_state(connection, id_asignacion, nuevo_estado, observacion)
                self.movimientos.insert(
                    self._tipo_movimiento(nuevo_estado),
                    (
                        f"{self._tipo_movimiento(nuevo_estado)}: {asignacion.get('objeto', '')} "
                        f"para la matrícula {asignacion.get('matricula', '')}."
                    ),
                    int(asignacion["id_empleado"]),
                    connection,
                    id_objeto=int(asignacion["id_objeto"]),
                    id_asignacion=id_asignacion,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    observacion=observacion,
                )
                connection.commit()
                return {"ok": True, "mensaje": "Asignación actualizada correctamente."}
            except Exception as exc:  # noqa: BLE001
                connection.rollback()
                return {"ok": False, "mensaje": f"No fue posible actualizar la asignación: {exc}"}

    def actualizar_observacion_asignacion(self, id_asignacion: int, observacion: str) -> dict:
        with get_connection() as connection:
            try:
                asignacion = self.repository.get_by_id(connection, id_asignacion)
                if not asignacion:
                    return {"ok": False, "mensaje": "No se encontró la asignación seleccionada."}
                self.repository.update_assignment_observation(connection, id_asignacion, observacion)
                self.movimientos.insert(
                    "Observación actualizada",
                    (
                        f"Observación actualizada para {asignacion.get('objeto', '')} "
                        f"de la matrícula {asignacion.get('matricula', '')}."
                    ),
                    int(asignacion["id_empleado"]),
                    connection,
                    id_objeto=int(asignacion["id_objeto"]),
                    id_asignacion=id_asignacion,
                    estado_anterior=asignacion.get("estado"),
                    estado_nuevo=asignacion.get("estado"),
                    observacion=observacion,
                )
                connection.commit()
                return {"ok": True, "mensaje": "Observación actualizada correctamente."}
            except Exception as exc:  # noqa: BLE001
                connection.rollback()
                return {"ok": False, "mensaje": f"No fue posible actualizar la observación: {exc}"}

    def generar_pendientes_por_empleado(self, id_empleado: int) -> dict:
        with get_connection() as connection:
            try:
                result = self._generar_pendientes_por_empleado(connection, id_empleado)
                connection.commit()
                return result
            except Exception as exc:  # noqa: BLE001 - mostrar error claro sin cerrar app
                connection.rollback()
                return self._error_result(f"Error al generar asignaciones para empleado {id_empleado}: {exc}")

    def generar_pendientes_para_empleados_activos(self) -> dict:
        summary = self._empty_summary()
        with get_connection() as connection:
            empleados = self.repository.list_active_employees_for_generation(connection)
            for empleado in empleados:
                savepoint = f"empleado_{empleado['id']}"
                try:
                    connection.execute(f"SAVEPOINT {savepoint}")
                    result = self._generar_pendientes_por_empleado(connection, int(empleado["id"]))
                    connection.execute(f"RELEASE {savepoint}")
                    self._merge_summary(summary, result)
                except Exception as exc:  # noqa: BLE001
                    connection.execute(f"ROLLBACK TO {savepoint}")
                    connection.execute(f"RELEASE {savepoint}")
                    summary["errores"].append(
                        {
                            "id_empleado": empleado.get("id"),
                            "matricula": empleado.get("matricula", ""),
                            "error": str(exc),
                        }
                    )
            connection.commit()

        diagnostic_path = save_asignaciones_diagnostic(summary)
        summary["ruta_diagnostico"] = str(diagnostic_path)
        return summary

    def generar_asignaciones_para_empleados_activos(self) -> dict:
        return self.generar_pendientes_para_empleados_activos()

    def _generar_pendientes_por_empleado(self, connection, id_empleado: int) -> dict:
        summary = self._empty_summary()
        empleado = self.repository.get_employee_for_generation(connection, id_empleado)
        if not empleado:
            summary["errores"].append({"id_empleado": id_empleado, "error": "El empleado no existe."})
            return summary

        detail = {
            "matricula": empleado.get("matricula", ""),
            "nombre": empleado.get("nombre", ""),
            "puesto": empleado.get("puesto", ""),
            "creadas": 0,
            "omitidas": 0,
            "observaciones": [],
        }
        summary["detalle_por_empleado"].append(detail)

        if empleado.get("estado") != "Activo":
            summary["empleados_omitidos"] += 1
            detail["observaciones"].append("El empleado está inactivo.")
            return summary
        if not empleado.get("id_puesto"):
            summary["empleados_sin_puesto"] += 1
            detail["observaciones"].append("El empleado no tiene puesto asignado.")
            return summary

        summary["empleados_procesados"] += 1
        reglas = self.repository.list_active_rules_for_position(connection, int(empleado["id_puesto"]))
        if not reglas:
            summary["puestos_sin_reglas"] += 1
            detail["observaciones"].append("El puesto del empleado no tiene reglas de asignación configuradas.")
            self.movimientos.insert(
                "Puesto sin reglas",
                f"El puesto {empleado.get('puesto', '')} no tiene reglas para la matrícula {empleado.get('matricula', '')}.",
                int(empleado["id"]),
                connection,
            )
            return summary

        for regla in reglas:
            objeto = regla.get("objeto", "")
            objeto_id = int(regla["id_objeto"])
            if int(regla.get("objeto_activo") or 0) != 1:
                summary["objetos_inactivos"] += 1
                detail["observaciones"].append(f"Objeto inactivo omitido: {objeto}.")
                continue

            existing = self.repository.find_existing_assignment(connection, int(empleado["id"]), objeto_id)
            if existing:
                summary["omitidas_por_duplicado"] += 1
                detail["omitidas"] += 1
                continue

            cantidad = max(int(regla.get("cantidad") or 1), 1)
            self.repository.create_assigned_assignment(
                connection,
                int(empleado["id"]),
                objeto_id,
                cantidad,
                "Asignacion registrada automaticamente por reglas puesto-objeto.",
            )
            summary["creadas"] += 1
            detail["creadas"] += 1
            self.movimientos.insert(
                "Asignacion generada",
                f"Se genero asignacion de {objeto} para la matricula {empleado.get('matricula', '')}.",
                int(empleado["id"]),
                connection,
            )

        if summary["creadas"]:
            self.movimientos.insert(
                "Generacion de asignaciones",
                (
                    f"Se generaron {detail['creadas']} asignaciones para la matricula "
                    f"{empleado.get('matricula', '')} segun el puesto {empleado.get('puesto', '')}."
                ),
                int(empleado["id"]),
                connection,
            )
        return summary

    def _empty_summary(self) -> dict:
        return {
            "empleados_procesados": 0,
            "empleados_omitidos": 0,
            "creadas": 0,
            "omitidas_por_duplicado": 0,
            "empleados_sin_puesto": 0,
            "puestos_sin_reglas": 0,
            "objetos_inactivos": 0,
            "errores": [],
            "detalle_por_empleado": [],
            "ruta_diagnostico": "",
        }

    def _error_result(self, message: str) -> dict:
        result = self._empty_summary()
        result["errores"].append({"error": message})
        return result

    def _merge_summary(self, target: dict, source: dict) -> None:
        for key in (
            "empleados_procesados",
            "empleados_omitidos",
            "creadas",
            "omitidas_por_duplicado",
            "empleados_sin_puesto",
            "puestos_sin_reglas",
            "objetos_inactivos",
        ):
            target[key] += int(source.get(key, 0))
        target["errores"].extend(source.get("errores", []))
        target["detalle_por_empleado"].extend(source.get("detalle_por_empleado", []))

    def _validar_transicion(self, asignacion: dict, nuevo_estado: str) -> str | None:
        estado_actual = asignacion.get("estado")
        if estado_actual == nuevo_estado:
            return "La asignación ya tiene ese estado."
        if estado_actual == "Pendiente":
            return None if nuevo_estado in {"Asignado", "No aplica"} else "Desde Pendiente solo puede marcarse como Asignado o No aplica."
        if estado_actual == "Asignado":
            requiere = int(asignacion.get("requiere_devolucion_valor") or 0) == 1
            if nuevo_estado == "Pendiente de devolución" and requiere:
                return None
            return "Esta asignación solo puede pasar a Pendiente de devolución cuando requiere devolución."
        if estado_actual == "Pendiente de devolución":
            return None if nuevo_estado == "Devuelto" else "Desde Pendiente de devolución solo puede marcarse como Devuelto."
        return "El estado actual no permite cambios operativos."

    def _tipo_movimiento(self, nuevo_estado: str) -> str:
        return {
            "Asignado": "Asignación marcada como asignada",
            "No aplica": "Asignación marcada como no aplica",
            "Pendiente de devolución": "Asignación marcada como pendiente de devolución",
            "Devuelto": "Asignación marcada como devuelta",
        }.get(nuevo_estado, "Asignación actualizada")
