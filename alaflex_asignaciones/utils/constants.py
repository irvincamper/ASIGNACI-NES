from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
LOGO_PATH = ASSETS_DIR / "logo_alaflex.png"
DATA_DIR = PROJECT_ROOT / "data"
EXPEDIENTES_DIR = DATA_DIR / "expedientes"
BACKUPS_DIR = DATA_DIR / "backups"
IMPORTAR_DIR = PROJECT_ROOT / "IMPORTAR"
IMPORT_DIAGNOSTICS_DIR = DATA_DIR / "import_diagnostics"
ASIGNACIONES_DIAGNOSTICS_DIR = DATA_DIR / "asignaciones_diagnostics"

FUTURE_DATABASE_PATH = DATA_DIR / "seguridad_salud.db"

MODULES = [
    {"key": "dashboard", "title": "Dashboard", "icon": "fa5s.home"},
    {"key": "empleados", "title": "Empleados", "icon": "fa5s.users"},
    {"key": "objetos", "title": "Objetos", "icon": "fa5s.cube"},
    {"key": "relaciones", "title": "Relación Puesto-Objetos", "icon": "fa5s.link"},
    {"key": "estacionamientos", "title": "Estacionamientos", "icon": "fa5s.parking"},
    {"key": "pdf", "title": "Vista previa PDF", "icon": "fa5s.file-pdf"},
]

MOCK_ACTION_MESSAGE = (
    "La lectura real desde SQLite y la importación inicial desde IMPORTAR ya están activas. "
    "Esta acción manual queda pendiente para la siguiente etapa."
)
