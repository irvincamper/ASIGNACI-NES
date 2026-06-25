from __future__ import annotations

from datetime import date, datetime
from math import ceil

from repositories.asignaciones_repository import AsignacionesRepository
from repositories.empleados_repository import EmpleadosRepository
from repositories.expedientes_repository import ExpedientesRepository
from utils.constants import IMPORTAR_DIR
from utils.normalizers import normalize_matricula


RECURSOS_POR_PAGINA_FORMATO = 16


class ExpedienteService:
    def __init__(self) -> None:
        self.empleados = EmpleadosRepository()
        self.asignaciones = AsignacionesRepository()
        self.expedientes = ExpedientesRepository()

    def get_preview_data(self) -> tuple[dict, list[dict]]:
        empleado = self.empleados.get_first()
        if not empleado:
            preview = {
                "id": 0,
                "matricula": "",
                "nombre": "",
                "motivo": "Contratacion",
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
            "motivo": "Contratacion",
            "puesto": empleado["puesto"],
            "puesto_anterior": "",
            "fecha": date.today().strftime("%d/%m/%Y"),
            "total_recursos": str(len(recursos)),
            "paginas": "1",
            "ruta": "Vista previa unicamente",
            "formato": "PDF",
            "reporte": "ALA-RH-FR-29",
            "revision": "2",
        }
        preview_rows = [
            {
                "no": str(index),
                "tipo": "X",
                "fecha": "",
                "categoria": row.get("categoria", ""),
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
            raise ValueError("No se encontro un empleado con esa matricula.")
        asignaciones = self.asignaciones.list_for_employee(int(empleado["id_empleado"]))
        recursos = self._recursos_para_motivo(asignaciones, motivo)
        if not recursos:
            raise ValueError("El empleado no tiene asignaciones para generar el expediente.")
        plantilla = self._template_path()
        now = datetime.now()
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
            "fecha_generacion": now.isoformat(timespec="seconds"),
            "fecha_documento": now.strftime("%d/%m/%Y"),
            "asignaciones": asignaciones,
            "objetos_asignados": recursos,
            "recursos": recursos,
            "total_recursos": len(recursos),
            "total_objetos": len(recursos),
            "paginas": max(2, ceil(len(recursos) / RECURSOS_POR_PAGINA_FORMATO)),
            "revision": "2",
            "estacionamiento": empleado.get("estacionamiento", "-"),
            "locker": empleado.get("locker", "-"),
            "plantilla_detectada": plantilla is not None,
            "ruta_plantilla": str(plantilla) if plantilla else "",
        }

    def registrar_expediente_generado(self, json_snapshot: dict, ruta_pdf: str) -> int:
        return self.expedientes.insert_generated(json_snapshot, ruta_pdf)

    def listar_expedientes_por_matricula(self, matricula: str) -> list[dict]:
        matricula = normalize_matricula(matricula)
        if not matricula:
            return []
        return self.expedientes.list_by_matricula(matricula)

    def _recursos_para_motivo(self, asignaciones: list[dict], motivo: str) -> list[dict]:
        if motivo == "Baja":
            return [
                self._decorate_recurso(item, devolucion=True)
                for item in asignaciones
                if item.get("requiere_devolucion") in {"Si", "Sí", "SÃ­"}
            ]
        return [self._decorate_recurso(item, devolucion=False) for item in asignaciones]

    def _decorate_recurso(self, item: dict, devolucion: bool) -> dict:
        return {
            **item,
            "tipo_operacion": "Devolucion" if devolucion else "Asignacion",
            "unidad": item.get("unidad") or "",
        }

    def _template_path(self):
        matches = list(IMPORTAR_DIR.glob("FORMATO ENTREGA-RECEPCI*.xlsx"))
        return matches[0] if matches else None
