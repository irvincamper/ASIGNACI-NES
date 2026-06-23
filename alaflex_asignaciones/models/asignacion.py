from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Asignacion:
    id: int
    id_empleado: int
    id_objeto: int
    cantidad: int
    tipo_movimiento: str
    estado: str
    fecha_asignacion: str | None = None
    fecha_devolucion: str | None = None
    observaciones: str | None = None
