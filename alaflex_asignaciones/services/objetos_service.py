from __future__ import annotations

from repositories.objetos_repository import ObjetosRepository


class ObjetosService:
    def __init__(self) -> None:
        self.repository = ObjetosRepository()

    def get_kpis(self) -> list[dict]:
        data = self.repository.kpis()
        return [
            {"title": "Total objetos", "value": str(data["total"]), "icon": "fa5s.cube", "color": "#0057E7"},
            {"title": "Con devoluciÃ³n", "value": str(data["con_devolucion"]), "icon": "fa5s.undo", "color": "#F59E0B"},
            {"title": "Activos", "value": str(data["activos"]), "icon": "fa5s.check-circle", "color": "#16A05D"},
        ]

    def list_objetos(self, search: str = "", categoria: str = "Todas las categorÃ­as", estado: str = "Todos los estados") -> list[dict]:
        rows = self.repository.list_summary(search=search.strip(), categoria=categoria, estado=estado)
        return rows

    def list_categories(self) -> list[str]:
        return ["Todas las categorÃ­as", *self.repository.list_categories()]

    def guardar_objeto(
        self,
        data: dict,
        objeto_id: int | None = None,
    ) -> dict:
        nombre = str(data.get("nombre", "")).strip()
        categoria = str(data.get("categoria", "")).strip()
        if not nombre:
            return {"ok": False, "mensaje": "Ingresa el nombre del objeto."}
        if not categoria:
            return {"ok": False, "mensaje": "Ingresa la categoría del objeto."}
        if self.repository.find_by_name(nombre, objeto_id):
            return {"ok": False, "mensaje": "Ya existe un objeto con ese nombre."}
        requiere_devolucion = 1 if data.get("requiere_devolucion") in {"Sí", "Si", True, 1} else 0
        activo = 1 if data.get("estado") == "Activo" else 0
        observaciones = str(data.get("observaciones", "")).strip()
        if objeto_id:
            self.repository.update(objeto_id, nombre, categoria, requiere_devolucion, activo, observaciones)
            return {"ok": True, "mensaje": "Objeto actualizado correctamente."}
        self.repository.create(nombre, categoria, requiere_devolucion, activo, observaciones)
        return {"ok": True, "mensaje": "Objeto creado correctamente."}

    def desactivar_objeto(self, objeto_id: int) -> dict:
        self.repository.deactivate(objeto_id)
        return {"ok": True, "mensaje": "Objeto desactivado correctamente."}
