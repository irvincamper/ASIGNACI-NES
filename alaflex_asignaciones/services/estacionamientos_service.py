from __future__ import annotations

from repositories.estacionamientos_repository import EstacionamientosRepository
from utils.normalizers import normalize_matricula


class EstacionamientosService:
    def __init__(self) -> None:
        self.repository = EstacionamientosRepository()

    def get_kpis(self) -> list[dict]:
        total = self.repository.total()
        libres = self.repository.count_by_estado("Libre")
        ocupados = self.repository.count_by_estado("Ocupado")
        conflictos = self.repository.count_by_estado("Conflicto")
        return [
            {"title": "Totales", "value": str(total), "icon": "fa5s.parking", "color": "#0057E7"},
            {"title": "Libres", "value": str(libres), "icon": "fa5s.parking", "color": "#16A05D"},
            {"title": "Ocupados", "value": str(ocupados), "icon": "fa5s.car", "color": "#7C3AED"},
            {"title": "Conflictos", "value": str(conflictos), "icon": "fa5s.exclamation-triangle", "color": "#E11D48"},
        ]

    def list_estacionamientos(self, search: str = "", estado: str = "Todos los estados") -> list[dict]:
        return self.repository.list_summary(search=search.strip(), estado=estado)

    def preparar_asignacion(self, matricula: str, cajon: str) -> dict:
        matricula = normalize_matricula(matricula)
        if not matricula:
            return {"ok": False, "mensaje": "La matrícula es obligatoria."}
        empleado = self.repository.get_employee_by_matricula(matricula)
        if not empleado:
            return {"ok": False, "mensaje": "No se encontró un empleado con esa matrícula."}
        if empleado.get("estado") != "Activo":
            return {"ok": False, "mensaje": "El empleado seleccionado no está activo."}
        parking = self.repository.get_by_cajon(cajon)
        if not parking:
            return {"ok": False, "mensaje": "No se encontró el cajón seleccionado."}
        if parking.get("estado") != "Libre":
            return {"ok": False, "mensaje": "El cajón está ocupado."}
        existing = self.repository.get_employee_parking(int(empleado["id"]))
        return {"ok": True, "empleado": empleado, "estacionamiento_actual": existing}

    def asignar(self, data: dict, *, replace_existing: bool = False) -> dict:
        matricula = normalize_matricula(str(data.get("matricula", "")))
        cajon = str(data.get("cajon", "")).strip()
        tipo = str(data.get("tipo_asignacion", "")).strip() or "Empleado"
        observaciones = str(data.get("observaciones", "")).strip()
        prepared = self.preparar_asignacion(matricula, cajon)
        if not prepared.get("ok"):
            return prepared
        existing = prepared.get("estacionamiento_actual")
        if existing and not replace_existing:
            return {
                "ok": False,
                "requiere_confirmacion": True,
                "mensaje": f"El empleado ya tiene asignado el cajón {existing.get('cajon')}. ¿Deseas reemplazarlo?",
            }
        self.repository.assign(cajon, int(prepared["empleado"]["id"]), tipo, observaciones, replace_existing=bool(existing))
        return {"ok": True, "mensaje": "Estacionamiento asignado correctamente."}

    def liberar(self, cajon: str, observaciones: str = "") -> dict:
        parking = self.repository.get_by_cajon(cajon)
        if not parking:
            return {"ok": False, "mensaje": "No se encontró el cajón seleccionado."}
        if parking.get("estado") == "Libre":
            return {"ok": False, "mensaje": "El cajón ya se encuentra libre."}
        self.repository.release(cajon, observaciones.strip())
        return {"ok": True, "mensaje": "Estacionamiento liberado correctamente."}

    def detalle(self, cajon: str) -> dict:
        parking = self.repository.get_by_cajon(cajon)
        if not parking:
            return {"ok": False, "mensaje": "No se encontró información."}
        return {"ok": True, "detalle": parking}
