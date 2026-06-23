from __future__ import annotations

from database.connection import get_connection
from repositories.asignaciones_repository import AsignacionesRepository
from repositories.movimientos_repository import MovimientosRepository
from utils.asignaciones_diagnostics import save_asignaciones_diagnostic


class AsignacionesService:
    def __init__(self) -> None:
        self.repository = AsignacionesRepository()
        self.movimientos = MovimientosRepository()

    def list_for_employee(self, empleado_id: int) -> list[dict]:
        return self.repository.list_for_employee(empleado_id)

    def generar_pendientes_por_empleado(self, id_empleado: int) -> dict:
        with get_connection() as connection:
            try:
                result = self._generar_pendientes_por_empleado(connection, id_empleado)
                connection.commit()
                return result
            except Exception as exc:  # noqa: BLE001 - mostrar error claro sin cerrar app
                connection.rollback()
                return self._error_result(f"Error al generar pendientes para empleado {id_empleado}: {exc}")

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

            if int(regla.get("stock_disponible") or 0) <= 0:
                summary["objetos_sin_stock"] += 1
                detail["observaciones"].append(f"Objeto sin stock disponible: {objeto}.")

            cantidad = max(int(regla.get("cantidad") or 1), 1)
            self.repository.create_pending_assignment(
                connection,
                int(empleado["id"]),
                objeto_id,
                cantidad,
                int(regla.get("requiere_devolucion") or 1),
                "Asignación pendiente generada automáticamente por reglas puesto-objeto.",
            )
            summary["creadas"] += 1
            detail["creadas"] += 1
            self.movimientos.insert(
                "Asignación pendiente generada",
                f"Se generó asignación pendiente de {objeto} para la matrícula {empleado.get('matricula', '')}.",
                int(empleado["id"]),
                connection,
            )

        if summary["creadas"]:
            self.movimientos.insert(
                "Generación de asignaciones pendientes",
                (
                    f"Se generaron {detail['creadas']} asignaciones pendientes para la matrícula "
                    f"{empleado.get('matricula', '')} según el puesto {empleado.get('puesto', '')}."
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
            "objetos_sin_stock": 0,
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
            "objetos_sin_stock",
        ):
            target[key] += int(source.get(key, 0))
        target["errores"].extend(source.get("errores", []))
        target["detalle_por_empleado"].extend(source.get("detalle_por_empleado", []))
