from __future__ import annotations

from repositories.asignaciones_repository import AsignacionesRepository
from repositories.empleados_repository import EmpleadosRepository
from repositories.estacionamientos_repository import EstacionamientosRepository
from repositories.lockers_repository import LockersRepository
from repositories.objetos_repository import ObjetosRepository
from repositories.relaciones_repository import RelacionesRepository


class DashboardService:
    def __init__(self) -> None:
        self.empleados = EmpleadosRepository()
        self.asignaciones = AsignacionesRepository()
        self.estacionamientos = EstacionamientosRepository()
        self.lockers = LockersRepository()
        self.objetos = ObjetosRepository()
        self.relaciones = RelacionesRepository()

    def get_kpis(self) -> list[dict]:
        activos = self.empleados.count_activos()
        asignados = self.asignaciones.count_asignadas()
        pendientes = self.asignaciones.count_by_estado("Pendiente")
        libres = self.estacionamientos.count_by_estado("Libre")
        ocupados = self.estacionamientos.count_by_estado("Ocupado")
        conflictos = self.estacionamientos.count_by_estado("Conflicto")
        return [
            {"title": "Empleados activos", "value": str(activos), "icon": "fa5s.users", "color": "#0057E7"},
            {"title": "Objetos asignados", "value": str(asignados), "icon": "fa5s.cube", "color": "#16A05D"},
            {"title": "Pendientes", "value": str(pendientes), "icon": "fa5s.clock", "color": "#F59E0B"},
            {"title": "Estacionamientos libres", "value": str(libres), "icon": "fa5s.parking", "color": "#0057E7"},
            {"title": "Estacionamientos ocupados", "value": str(ocupados), "icon": "fa5s.car", "color": "#7C3AED"},
            {"title": "Conflictos", "value": str(conflictos), "icon": "fa5s.exclamation-triangle", "color": "#E11D48"},
        ]

    def get_alerts(self) -> list[dict]:
        pendientes = self.asignaciones.count_by_estado("Pendiente")
        conflictos = self.estacionamientos.count_by_estado("Conflicto")
        ocupados = self.estacionamientos.count_by_estado("Ocupado")
        lockers = self.lockers.count_ocupados()
        sin_asignaciones = self.asignaciones.count_empleados_activos_sin_asignaciones()
        puestos_sin_reglas = self.relaciones.count_puestos_sin_reglas()
        objetos_inactivos = self.relaciones.count_objetos_inactivos_en_reglas()
        objetos_sin_stock = self.objetos.count_sin_stock()
        return [
            {"text": "Conflictos de estacionamiento por mismo turno.", "value": str(conflictos), "icon": "fa5s.exclamation-triangle", "color": "#E11D48"},
            {"text": "Asignaciones pendientes de validación inicial.", "value": str(pendientes), "icon": "fa5s.clock", "color": "#F59E0B"},
            {"text": "Empleados activos sin asignaciones generadas.", "value": str(sin_asignaciones), "icon": "fa5s.users", "color": "#0057E7"},
            {"text": "Puestos sin reglas de asignación.", "value": str(puestos_sin_reglas), "icon": "fa5s.link", "color": "#E11D48"},
            {"text": "Objetos inactivos en reglas.", "value": str(objetos_inactivos), "icon": "fa5s.ban", "color": "#E11D48"},
            {"text": "Objetos sin stock disponible.", "value": str(objetos_sin_stock), "icon": "fa5s.exclamation-circle", "color": "#F59E0B"},
            {"text": "Estacionamientos ocupados actualmente.", "value": str(ocupados), "icon": "fa5s.parking", "color": "#0057E7"},
            {"text": "Lockers ocupados actualmente.", "value": str(lockers), "icon": "fa5s.archive", "color": "#7C3AED"},
        ]
