from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Objeto:
    id: int
    nombre: str
    categoria: str
    stock_total: int
    stock_disponible: int
    requiere_devolucion: bool
    activo: bool = True
