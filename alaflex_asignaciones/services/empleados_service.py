from __future__ import annotations

from repositories.asignaciones_repository import AsignacionesRepository
from repositories.empleados_repository import EmpleadosRepository
from utils.normalizers import normalize_matricula


class EmpleadosService:
    def __init__(self) -> None:
        self.repository = EmpleadosRepository()
        self.asignaciones = AsignacionesRepository()

    def list_empleados(self, search: str = "", estado: str = "Estado: Todos") -> list[dict]:
        normalized = "Todos" if estado == "Estado: Todos" else estado
        return self.repository.list_summary(search=search.strip(), estado=normalized)

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
        empleado["total_asignaciones"] = len(asignaciones)
        empleado["asignados"] = sum(int(item.get("cantidad") or 0) for item in asignaciones if item.get("estado") == "Asignado")
        empleado["pendientes"] = sum(int(item.get("cantidad") or 0) for item in asignaciones if item.get("estado") == "Pendiente")
        empleado["pendientes_de_devolucion"] = sum(
            int(item.get("cantidad") or 0) for item in asignaciones if item.get("estado") == "Pendiente de devolución"
        )
        return empleado
