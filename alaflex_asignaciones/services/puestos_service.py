from __future__ import annotations

from repositories.puestos_repository import PuestosRepository


class PuestosService:
    def __init__(self) -> None:
        self.repository = PuestosRepository()

    def list_active(self) -> list[dict]:
        return self.repository.list_active()
