from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.constants import ASIGNACIONES_DIAGNOSTICS_DIR


def save_asignaciones_diagnostic(summary: dict[str, Any]) -> Path:
    ASIGNACIONES_DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = ASIGNACIONES_DIAGNOSTICS_DIR / f"asignaciones_pendientes_{stamp}.json"
    payload = {"fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **summary}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
