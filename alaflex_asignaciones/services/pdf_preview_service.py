from __future__ import annotations

from datetime import date

from services.empleados_service import EmpleadosService
from services.expediente_service import ExpedienteService
from utils.constants import IMPORTAR_DIR
from utils.normalizers import normalize_matricula


RECURSOS_POR_PAGINA_FORMATO = 16


class PdfPreviewService:
    def __init__(self) -> None:
        self.empleados = EmpleadosService()
        self.expediente = ExpedienteService()

    def construir_preview_data(self, matricula: str, motivo: str) -> dict:
        matricula = normalize_matricula(matricula)
        if not matricula:
            return {"ok": False, "mensaje": "Ingresa una matrícula para continuar."}
        empleado = self.empleados.buscar_por_matricula(matricula)
        if not empleado:
            return {"ok": False, "mensaje": "No se encontró un empleado con esa matrícula."}
        if empleado.get("estado") == "Inactivo" and motivo != "Baja":
            return {
                "ok": False,
                "empleado": empleado,
                "mensaje": "El empleado está inactivo. Solo puede generarse preview si el motivo es Baja.",
            }

        try:
            json_expediente = self.expediente.construir_json_expediente(matricula, motivo)
        except ValueError as exc:
            return {"ok": False, "empleado": empleado, "mensaje": str(exc)}
        recursos = json_expediente.get("recursos", [])
        plantilla = self._template_path()
        paginas_estimadas = int(
            json_expediente.get("paginas")
            or max(2, (len(recursos) + RECURSOS_POR_PAGINA_FORMATO - 1) // RECURSOS_POR_PAGINA_FORMATO)
        )
        return {
            "ok": True,
            "empleado": empleado,
            "matricula": empleado["matricula"],
            "nombre": empleado["nombre"],
            "puesto": empleado.get("puesto", ""),
            "turno": empleado.get("turno", ""),
            "estado": empleado.get("estado", ""),
            "motivo": motivo,
            "fecha": json_expediente.get("fecha_documento", date.today().strftime("%d/%m/%Y")),
            "recursos": recursos,
            "total_recursos": len(recursos),
            "paginas_estimadas": paginas_estimadas,
            "plantilla_detectada": plantilla is not None,
            "ruta_plantilla": str(plantilla) if plantilla else "",
            "mensaje": "Vista previa generada con datos reales.",
            "json_preliminar": json_expediente,
        }

    def empty_preview(self) -> dict:
        return {
            "ok": False,
            "empleado": {},
            "matricula": "",
            "nombre": "",
            "puesto": "",
            "turno": "",
            "estado": "",
            "motivo": "Contratación",
            "fecha": date.today().strftime("%d/%m/%Y"),
            "recursos": [],
            "total_recursos": 0,
            "paginas_estimadas": 2,
            "plantilla_detectada": self._template_path() is not None,
            "ruta_plantilla": str(self._template_path() or ""),
            "mensaje": "",
            "json_preliminar": {},
        }

    def _template_path(self):
        matches = list(IMPORTAR_DIR.glob("FORMATO ENTREGA-RECEPCI*.xlsx"))
        return matches[0] if matches else None
