from __future__ import annotations

from datetime import date

from repositories.asignaciones_repository import AsignacionesRepository
from repositories.empleados_repository import EmpleadosRepository
from utils.constants import IMPORTAR_DIR
from utils.normalizers import normalize_matricula


class ExpedienteService:
    def __init__(self) -> None:
        self.empleados = EmpleadosRepository()
        self.asignaciones = AsignacionesRepository()

    def get_preview_data(self) -> tuple[dict, list[dict]]:
        empleado = self.empleados.get_first()
        if not empleado:
            preview = {
                "id": 0,
                "matricula": "",
                "nombre": "",
                "motivo": "Contratación",
                "puesto": "",
                "puesto_anterior": "",
                "fecha": date.today().strftime("%d/%m/%Y"),
                "total_recursos": "0",
                "paginas": "1",
                "ruta": "",
                "formato": "PDF",
                "reporte": "ALA-RH-FR-29",
                "revision": "2",
            }
            return preview, []

        recursos = self.asignaciones.list_for_employee(int(empleado["id"]))
        preview = {
            "id": empleado["id"],
            "matricula": empleado["matricula"],
            "nombre": empleado["nombre"].upper(),
            "motivo": "Contratación",
            "puesto": empleado["puesto"],
            "puesto_anterior": "",
            "fecha": date.today().strftime("%d/%m/%Y"),
            "total_recursos": str(len(recursos)),
            "paginas": "1",
            "ruta": "Vista previa únicamente",
            "formato": "PDF",
            "reporte": "ALA-RH-FR-29",
            "revision": "2",
        }
        preview_rows = [
            {
                "no": str(index),
                "tipo": "X",
                "fecha": "",
                "categoria": "",
                "descripcion": row["concepto"],
                "cantidad": str(row["cantidad"]),
                "unidad": "",
                "firma": "",
            }
            for index, row in enumerate(recursos, start=1)
        ]
        return preview, preview_rows

    def construir_json_expediente(self, matricula: str, motivo: str) -> dict:
        matricula = normalize_matricula(matricula)
        empleado = self.empleados.get_profile_by_matricula(matricula)
        if not empleado:
            raise ValueError("No se encontró un empleado con esa matrícula.")
        asignaciones = self.asignaciones.list_for_employee(int(empleado["id_empleado"]))
        plantilla = self._template_path()
        return {
            "empleado": {
                "id_empleado": empleado["id_empleado"],
                "matricula": empleado["matricula"],
                "nombre": empleado["nombre"],
            },
            "motivo": motivo,
            "puesto": empleado.get("puesto", ""),
            "turno": empleado.get("turno", ""),
            "estado": empleado.get("estado", ""),
            "fecha_generacion": date.today().isoformat(),
            "asignaciones": asignaciones,
            "pendientes": empleado.get("pendientes", 0),
            "pendientes_de_devolucion": empleado.get("pendientes_de_devolucion", 0),
            "estacionamiento": empleado.get("estacionamiento", "-"),
            "locker": empleado.get("locker", "-"),
            "plantilla_detectada": plantilla is not None,
            "ruta_plantilla": str(plantilla) if plantilla else "",
        }

    def _template_path(self):
        matches = list(IMPORTAR_DIR.glob("FORMATO ENTREGA-RECEPCI*.xlsx"))
        return matches[0] if matches else None
