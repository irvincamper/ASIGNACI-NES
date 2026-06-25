from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Objeto:
    id: int
    nombre: str
    categoria: str
    requiere_devolucion: bool
    activo: bool = True
    observaciones: str | None = None
