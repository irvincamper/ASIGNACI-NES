from __future__ import annotations

from services.expediente_service import ExpedienteService


class ExpedienteMetadataService:
    def __init__(self) -> None:
        self.expedientes = ExpedienteService()

    def registrar(self, json_snapshot: dict, ruta_pdf: str) -> int:
        return self.expedientes.registrar_expediente_generado(json_snapshot, ruta_pdf)

    def listar_por_matricula(self, matricula: str) -> list[dict]:
        return self.expedientes.listar_expedientes_por_matricula(matricula)
