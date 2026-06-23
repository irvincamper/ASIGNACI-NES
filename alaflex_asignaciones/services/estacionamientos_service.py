from __future__ import annotations

from repositories.estacionamientos_repository import EstacionamientosRepository


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
