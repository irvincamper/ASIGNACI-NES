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

    def list_relaciones(self, puesto_id: int | None = None) -> list[dict]:
        return self.repository.list_by_puesto(puesto_id)
