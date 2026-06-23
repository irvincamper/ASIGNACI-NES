from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Estacionamiento:
    id: int
    cajon: str
    estado: str
    id_empleado: int | None = None
    tipo_asignacion: str | None = None
    turno_compartido: bool = False
    observaciones: str | None = None
