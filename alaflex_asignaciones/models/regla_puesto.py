from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReglaPuesto:
    id: int
    id_puesto: int
    id_objeto: int
    cantidad: int
    obligatorio: bool
    requiere_devolucion: bool
    activo: bool = True
