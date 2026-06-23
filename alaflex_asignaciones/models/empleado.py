from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Empleado:
    id: int
    matricula: str
    nombre: str
    id_puesto: int
    turno: str
    fecha_ingreso: str
    estado: str
    fecha_baja: str | None = None
    observaciones: str | None = None
