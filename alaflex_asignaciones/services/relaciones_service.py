from __future__ import annotations

from repositories.puestos_repository import PuestosRepository
from repositories.relaciones_repository import RelacionesRepository


class RelacionesService:
    def __init__(self) -> None:
        self.repository = RelacionesRepository()
        self.puestos_repository = PuestosRepository()

    def get_kpis(self) -> list[dict]:
        data = self.repository.kpis()
        return [
            {"title": "Total relaciones", "value": str(data["total"]), "icon": "fa5s.link", "color": "#0057E7"},
            {"title": "Obligatorias", "value": str(data["obligatorias"]), "icon": "fa5s.shield-alt", "color": "#16A05D"},
            {"title": "Con devolución", "value": str(data["con_devolucion"]), "icon": "fa5s.sync-alt", "color": "#F59E0B"},
        ]

    def list_puestos(self) -> list[dict]:
        return self.puestos_repository.list_active()

    def list_objetos(self) -> list[dict]:
        return self.repository.list_active_objects()

    def list_relaciones(self, puesto_id: int | None = None) -> list[dict]:
        return self.repository.list_by_puesto(puesto_id)

    def guardar_relacion(self, data: dict, relation_id: int | None = None) -> dict:
        puesto_id = data.get("id_puesto")
        objeto_id = data.get("id_objeto")
        try:
            cantidad = int(data.get("cantidad") or 0)
        except (TypeError, ValueError):
            cantidad = 0
        if not puesto_id:
            return {"ok": False, "mensaje": "Selecciona un puesto."}
        if not objeto_id:
            return {"ok": False, "mensaje": "Selecciona un objeto."}
        if cantidad <= 0:
            return {"ok": False, "mensaje": "La cantidad debe ser mayor a 0."}
        existing = self.repository.get_existing(int(puesto_id), int(objeto_id))
        if existing and int(existing["id"]) != int(relation_id or 0):
            if relation_id:
                return {"ok": False, "mensaje": "Ya existe una relación registrada para este puesto y objeto."}
            if int(existing["activo"] or 0) == 1:
                return {"ok": False, "mensaje": "Ya existe una relación activa para este puesto y objeto."}
        payload = {
            "id_puesto": int(puesto_id),
            "id_objeto": int(objeto_id),
            "cantidad": cantidad,
            "obligatorio": 1 if data.get("obligatorio") in {"Sí", "Si", True, 1} else 0,
            "requiere_devolucion": 1 if data.get("requiere_devolucion") in {"Sí", "Si", True, 1} else 0,
            "activo": 1 if data.get("estado") == "Activo" else 0,
        }
        self.repository.upsert(payload, relation_id)
        return {"ok": True, "mensaje": "Relación guardada correctamente."}

    def desactivar_relacion(self, relation_id: int) -> dict:
        self.repository.deactivate(relation_id)
        return {"ok": True, "mensaje": "Relación desactivada correctamente."}
