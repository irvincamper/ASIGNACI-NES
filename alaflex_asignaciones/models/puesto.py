from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Puesto:
    id: int
    nombre: str
    activo: bool = True
