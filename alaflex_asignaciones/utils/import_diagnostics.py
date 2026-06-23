from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.constants import IMPORT_DIAGNOSTICS_DIR


class ImportDiagnostics:
    def __init__(self) -> None:
        self.started_at = datetime.now()
        self.files_detected: list[str] = []
        self.files_missing: list[str] = []
        self.files_ignored: list[str] = []
        self.sheets_detected: list[str] = []
        self.sheets_missing: list[str] = []
        self.columns_detected: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.counters: dict[str, int] = defaultdict(int)
        self.template_detected = False

    def detected_file(self, name: str) -> None:
        self.files_detected.append(name)

    def missing_file(self, name: str) -> None:
        self.files_missing.append(name)

    def ignored_file(self, name: str) -> None:
        self.files_ignored.append(name)

    def detected_sheet(self, file_name: str, sheet_name: str) -> None:
        self.sheets_detected.append(f"{file_name} -> {sheet_name}")

    def missing_sheet(self, file_name: str, sheet_name: str) -> None:
        self.sheets_missing.append(f"{file_name} -> {sheet_name}")

    def detected_columns(self, file_name: str, sheet_name: str, columns: list[str]) -> None:
        visible = ", ".join(column for column in columns if column)
        self.columns_detected.append(f"{file_name} -> {sheet_name}: {visible}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def inc(self, key: str, amount: int = 1) -> None:
        self.counters[key] += amount

    def save(self) -> Path:
        IMPORT_DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = self.started_at.strftime("%Y%m%d_%H%M%S")
        path = IMPORT_DIAGNOSTICS_DIR / f"importacion_{stamp}.txt"
        lines = [
            "ALAFLEX - Diagnóstico de importación inicial",
            f"Fecha: {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "[Archivos detectados]",
            *self._items_or_dash(self.files_detected),
            "",
            "[Archivos faltantes]",
            *self._items_or_dash(self.files_missing),
            "",
            "[Archivos extra ignorados]",
            *self._items_or_dash(self.files_ignored),
            "",
            "[Hojas detectadas]",
            *self._items_or_dash(self.sheets_detected),
            "",
            "[Hojas faltantes]",
            *self._items_or_dash(self.sheets_missing),
            "",
            "[Columnas detectadas]",
            *self._items_or_dash(self.columns_detected),
            "",
            "[Resumen]",
            *self._counter_lines(),
            f"Plantilla FORMATO ENTREGA-RECEPCIÓN.xlsx detectada: {'Sí' if self.template_detected else 'No'}",
            "",
            "[Advertencias]",
            *self._items_or_dash(self.warnings),
            "",
            "[Errores no bloqueantes]",
            *self._items_or_dash(self.errors),
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _counter_lines(self) -> list[str]:
        if not self.counters:
            return ["- Sin movimientos registrados"]
        return [f"- {key}: {value}" for key, value in sorted(self.counters.items())]

    @staticmethod
    def _items_or_dash(items: list[Any]) -> list[str]:
        if not items:
            return ["- Ninguno"]
        return [f"- {item}" for item in items]
