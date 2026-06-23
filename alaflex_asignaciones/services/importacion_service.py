from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repositories.importacion_repository import ImportacionRepository
from utils.constants import IMPORTAR_DIR
from utils.excel_reader import find_header_row, get_sheet_by_name, open_workbook_readonly, rows_as_dicts
from utils.import_diagnostics import ImportDiagnostics
from utils.normalizers import (
    clean_text,
    default_requires_return,
    make_lookup_key,
    marked_as_assigned,
    normalize_estado_estacionamiento,
    normalize_estado_locker,
    normalize_header,
    normalize_identifier,
    normalize_matricula,
    normalize_turno,
)


@dataclass
class ImportacionResult:
    imported_real_data: bool
    diagnostics_path: Path | None


EXPECTED_FILES = {
    "personal_activo": "PERSONAL ACTIVO 2026.xlsx",
    "personal_semana": "PERSONAL DE LA SEMANA 25.xlsx",
    "asignaciones_puesto": "ASIGNACIONES POR PUESTO 2026.xlsx",
    "control_lockers_estacionamiento": "CONTROL DE LOCKERS-ESTACIONAMIENTO.xlsx",
    "formato_entrega_recepcion": "FORMATO ENTREGA-RECEPCIÓN.xlsx",
}


def importar_datos_iniciales_desde_importar(connection: sqlite3.Connection) -> ImportacionResult:
    diagnostics = ImportDiagnostics()
    try:
        files = _discover_files(diagnostics)
        operational_files = [
            files.get("personal_activo"),
            files.get("personal_semana"),
            files.get("asignaciones_puesto"),
            files.get("control_lockers_estacionamiento"),
        ]
        if files.get("formato_entrega_recepcion"):
            diagnostics.template_detected = True
            diagnostics.inc("plantillas_pdf_detectadas")
            diagnostics.warn("FORMATO ENTREGA-RECEPCIÓN.xlsx fue detectado solo como plantilla futura del módulo 6.")
        if not any(operational_files):
            diagnostics.warn("No se encontraron archivos operativos válidos en IMPORTAR. Se usará seed ficticio si la base está vacía.")
            return ImportacionResult(False, diagnostics.save())

        repository = ImportacionRepository(connection)
        if repository.has_known_fallback_seed_only():
            repository.clear_importable_data()
            diagnostics.inc("seed ficticio limpiado")
            diagnostics.warn("Se detectó únicamente el seed ficticio de Etapa 2A y se limpió antes de importar datos reales.")
            repository = ImportacionRepository(connection)

        turnos = _load_turnos(files.get("personal_semana"), diagnostics)
        matriculas_padron = _import_personal_activo(files.get("personal_activo"), turnos, repository, diagnostics)
        _diagnose_turnos_sin_padron(turnos, matriculas_padron, diagnostics)
        _import_asignaciones_por_puesto(files.get("asignaciones_puesto"), repository, diagnostics)
        _import_lockers_estacionamientos(files.get("control_lockers_estacionamiento"), repository, diagnostics)

        imported_real_data = _has_real_import_data(diagnostics)
        diagnostics_path = diagnostics.save()
        print(f"[ALAFLEX][Importación] Diagnóstico generado: {diagnostics_path}")
        return ImportacionResult(imported_real_data, diagnostics_path)
    except Exception as exc:  # noqa: BLE001 - importación inicial no debe cerrar la app
        diagnostics.error(f"Error general no bloqueante en importación inicial: {exc}")
        diagnostics_path = diagnostics.save()
        print(f"[ALAFLEX][Importación] Error no bloqueante. Diagnóstico: {diagnostics_path}")
        return ImportacionResult(False, diagnostics_path)


def _discover_files(diagnostics: ImportDiagnostics) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not IMPORTAR_DIR.exists():
        for expected in EXPECTED_FILES.values():
            diagnostics.missing_file(expected)
        diagnostics.warn(f"No existe la carpeta IMPORTAR: {IMPORTAR_DIR}")
        return files

    candidates = [path for path in IMPORTAR_DIR.glob("*.xlsx") if not path.name.startswith("~$")]
    used: set[Path] = set()
    for path in candidates:
        key = normalize_header(path.stem)
        file_key = _file_key_from_name(key)
        if file_key:
            files[file_key] = path
            used.add(path)
            diagnostics.detected_file(path.name)
        else:
            diagnostics.ignored_file(path.name)

    for file_key, expected_name in EXPECTED_FILES.items():
        if file_key not in files:
            diagnostics.missing_file(expected_name)
    return files


def _file_key_from_name(normalized_stem: str) -> str | None:
    if "personal activo" in normalized_stem:
        return "personal_activo"
    if "personal de la semana" in normalized_stem:
        return "personal_semana"
    if "asignaciones por puesto" in normalized_stem:
        return "asignaciones_puesto"
    if "control de lockers estacionamiento" in normalized_stem:
        return "control_lockers_estacionamiento"
    if "formato entrega recepcion" in normalized_stem:
        return "formato_entrega_recepcion"
    return None


def _load_turnos(path: Path | None, diagnostics: ImportDiagnostics) -> dict[str, str]:
    if not path:
        return {}
    turnos: dict[str, str] = {}
    try:
        workbook = open_workbook_readonly(path)
        try:
            sheet = get_sheet_by_name(workbook, "Hoja1")
            if sheet is None:
                diagnostics.missing_sheet(path.name, "Hoja1")
                return turnos
            diagnostics.detected_sheet(path.name, sheet.title)
            header_row, headers = find_header_row(sheet, ["matricula", "turno"])
            if not header_row:
                diagnostics.error(f"{path.name}: no se detectaron columnas Matrícula y Turno.")
                return turnos
            diagnostics.detected_columns(path.name, sheet.title, headers)
            for item in rows_as_dicts(sheet, header_row):
                matricula = normalize_matricula(item.get("matricula"))
                if not matricula:
                    continue
                turno = normalize_turno(item.get("turno"))
                turnos[matricula] = turno
                diagnostics.inc("turnos leídos")
        finally:
            workbook.close()
    except Exception as exc:  # noqa: BLE001
        diagnostics.error(f"{path.name}: no se pudo leer turnos. {exc}")
    return turnos


def _import_personal_activo(
    path: Path | None,
    turnos: dict[str, str],
    repository: ImportacionRepository,
    diagnostics: ImportDiagnostics,
) -> set[str]:
    matriculas_padron: set[str] = set()
    if not path:
        return matriculas_padron
    try:
        workbook = open_workbook_readonly(path)
        try:
            sheet = get_sheet_by_name(workbook, "Activo26")
            if sheet is None:
                diagnostics.missing_sheet(path.name, "Activo26")
                return matriculas_padron
            diagnostics.detected_sheet(path.name, sheet.title)
            header_row, headers = find_header_row(sheet, ["matricula", "nombre", "puesto"])
            if not header_row:
                diagnostics.error(f"{path.name}: no se detectaron columnas Matrícula, Nombre y Puesto.")
                return matriculas_padron
            diagnostics.detected_columns(path.name, sheet.title, headers)
            for item in rows_as_dicts(sheet, header_row):
                row_number = int(item.get("_row_number") or 0)
                matricula = normalize_matricula(item.get("matricula"))
                nombre = clean_text(item.get("nombre"))
                puesto = clean_text(item.get("puesto"))
                clave_puesto = clean_text(item.get("clave puesto"), uppercase=True)

                if not matricula:
                    diagnostics.inc("empleados omitidos")
                    diagnostics.warn(f"{path.name} fila {row_number}: empleado omitido por matrícula vacía.")
                    continue
                if not nombre:
                    diagnostics.inc("empleados omitidos")
                    diagnostics.warn(f"{path.name} fila {row_number}: empleado {matricula} omitido por nombre vacío.")
                    continue
                if not puesto:
                    diagnostics.inc("empleados omitidos")
                    diagnostics.warn(f"{path.name} fila {row_number}: empleado {matricula} omitido por puesto vacío.")
                    continue

                turno = turnos.get(matricula, "Pendiente de revisión")
                if turno == "Pendiente de revisión":
                    diagnostics.inc("empleados sin turno")
                    diagnostics.warn(f"Empleado {matricula} no aparece en PERSONAL DE LA SEMANA 25.xlsx.")

                puesto_id, puesto_status = repository.upsert_puesto(puesto, clave_puesto)
                _count_status(diagnostics, "puestos", puesto_status)
                _, empleado_status = repository.upsert_empleado(matricula, nombre, puesto_id, turno)
                _count_status(diagnostics, "empleados", empleado_status)
                diagnostics.inc("filas empleados válidas")
                matriculas_padron.add(matricula)
        finally:
            workbook.close()
    except Exception as exc:  # noqa: BLE001
        diagnostics.error(f"{path.name}: no se pudo importar personal activo. {exc}")
    return matriculas_padron


def _diagnose_turnos_sin_padron(
    turnos: dict[str, str],
    matriculas_padron: set[str],
    diagnostics: ImportDiagnostics,
) -> None:
    for matricula in sorted(set(turnos) - matriculas_padron):
        diagnostics.inc("matrículas en turnos no encontradas en padrón")
        diagnostics.warn(f"Matrícula {matricula} aparece en turnos, pero no en PERSONAL ACTIVO 2026.xlsx.")


def _import_asignaciones_por_puesto(
    path: Path | None,
    repository: ImportacionRepository,
    diagnostics: ImportDiagnostics,
) -> None:
    if not path:
        return
    try:
        workbook = open_workbook_readonly(path)
        try:
            sheet = get_sheet_by_name(workbook, "Asignaciones")
            if sheet is None:
                diagnostics.missing_sheet(path.name, "Asignaciones")
                return
            diagnostics.detected_sheet(path.name, sheet.title)
            rows = sheet.iter_rows(min_row=1, values_only=True)
            try:
                category_row = list(next(rows))
                header_row = list(next(rows))
            except StopIteration:
                diagnostics.error(f"{path.name}: la hoja Asignaciones no tiene encabezados suficientes.")
                return

            headers = [normalize_header(value) for value in header_row]
            diagnostics.detected_columns(path.name, sheet.title, headers)
            try:
                puesto_col = headers.index("puesto")
            except ValueError:
                diagnostics.error(f"{path.name}: no se detectó columna Puesto.")
                return
            clave_col = headers.index("clave de puesto") if "clave de puesto" in headers else None

            object_columns = _build_object_columns(category_row, header_row, puesto_col, repository, diagnostics, path.name)
            if object_columns:
                diagnostics.warn(
                    f"{path.name}: no contiene stock/devolución por objeto; se usó stock 0 y devolución por defecto según categoría."
                )

            for row_number, row_values in enumerate(rows, start=3):
                row = list(row_values)
                puesto = clean_text(_cell(row, puesto_col))
                if not puesto:
                    continue
                clave = clean_text(_cell(row, clave_col), uppercase=True) if clave_col is not None else ""
                puesto_id, puesto_status = repository.upsert_puesto(puesto, clave)
                _count_status(diagnostics, "puestos", puesto_status)
                diagnostics.inc("filas puestos válidas")

                for column_index, objeto_id, requiere_devolucion in object_columns:
                    if marked_as_assigned(_cell(row, column_index)):
                        status = repository.upsert_regla(
                            puesto_id=puesto_id,
                            objeto_id=objeto_id,
                            cantidad=1,
                            obligatorio=1,
                            requiere_devolucion=requiere_devolucion,
                        )
                        _count_status(diagnostics, "relaciones", status)
        finally:
            workbook.close()
    except Exception as exc:  # noqa: BLE001
        diagnostics.error(f"{path.name}: no se pudo importar relación puesto-objeto. {exc}")


def _build_object_columns(
    category_row: list[Any],
    header_row: list[Any],
    puesto_col: int,
    repository: ImportacionRepository,
    diagnostics: ImportDiagnostics,
    file_name: str,
) -> list[tuple[int, int, int]]:
    object_columns: list[tuple[int, int, int]] = []
    last_category = "Otro"
    max_length = max(len(category_row), len(header_row))
    for index in range(max_length):
        category_value = clean_text(_cell(category_row, index))
        if category_value:
            last_category = category_value
        if index <= puesto_col:
            continue
        object_name = clean_text(_cell(header_row, index))
        if not object_name:
            continue
        category = last_category or "Otro"
        requiere_devolucion = default_requires_return(category)
        objeto_id, objeto_status = repository.upsert_objeto(
            nombre=object_name,
            categoria=category,
            stock_total=0,
            stock_disponible=0,
            requiere_devolucion=requiere_devolucion,
        )
        _count_status(diagnostics, "objetos", objeto_status)
        diagnostics.inc("objetos sin stock detectado")
        object_columns.append((index, objeto_id, requiere_devolucion))
    if not object_columns:
        diagnostics.warn(f"{file_name}: no se detectaron objetos en la matriz de asignación.")
    return object_columns


def _import_lockers_estacionamientos(
    path: Path | None,
    repository: ImportacionRepository,
    diagnostics: ImportDiagnostics,
) -> None:
    if not path:
        return
    try:
        workbook = open_workbook_readonly(path)
        try:
            sheet = get_sheet_by_name(workbook, "Control26_Loc_Est")
            if sheet is None:
                diagnostics.missing_sheet(path.name, "Control26_Loc_Est")
                return
            diagnostics.detected_sheet(path.name, sheet.title)
            header_row_index, headers = find_header_row(sheet, ["locker", "cajon"])
            if not header_row_index:
                diagnostics.error(f"{path.name}: no se detectaron secciones Locker y Cajón.")
                return
            diagnostics.detected_columns(path.name, sheet.title, headers)
            columns = _control_columns(headers)
            if not columns:
                diagnostics.error(f"{path.name}: no se pudieron mapear columnas de lockers/estacionamientos.")
                return

            seen_lockers: set[str] = set()
            seen_cajones: set[str] = set()
            for row_number, row_values in enumerate(
                sheet.iter_rows(min_row=header_row_index + 1, values_only=True),
                start=header_row_index + 1,
            ):
                row = list(row_values)
                _import_locker_row(path.name, row_number, row, columns, repository, diagnostics, seen_lockers)
                _import_estacionamiento_row(path.name, row_number, row, columns, repository, diagnostics, seen_cajones)
        finally:
            workbook.close()
    except Exception as exc:  # noqa: BLE001
        diagnostics.error(f"{path.name}: no se pudo importar lockers/estacionamientos. {exc}")


def _control_columns(headers: list[str]) -> dict[str, int] | None:
    locker_col = _index_of(headers, "locker")
    cajon_col = _index_of(headers, "cajon")
    if locker_col is None or cajon_col is None:
        return None

    locker_start = 0
    parking_start = cajon_col - 2 if cajon_col >= 2 else cajon_col
    return {
        "locker_matricula": _last_index_of(headers, "matricula", 0, locker_col),
        "locker_numero": locker_col,
        "locker_ubicacion": _first_index_of(headers, "ubicacion", locker_col, cajon_col),
        "locker_estado": _first_index_of(headers, "estatus", locker_col, cajon_col),
        "parking_matricula": _first_index_of(headers, "matricula", parking_start, cajon_col + 1),
        "parking_cajon": cajon_col,
        "parking_ubicacion": _first_index_of(headers, "ubicacion", cajon_col, len(headers)),
        "parking_estado": _first_index_of(headers, "estatus", cajon_col, len(headers)),
    }


def _import_locker_row(
    file_name: str,
    row_number: int,
    row: list[Any],
    columns: dict[str, int | None],
    repository: ImportacionRepository,
    diagnostics: ImportDiagnostics,
    seen_lockers: set[str],
) -> None:
    numero = normalize_identifier(_cell(row, columns.get("locker_numero")))
    if not numero:
        return
    numero_key = make_lookup_key(numero)
    if numero_key in seen_lockers:
        diagnostics.inc("duplicados ignorados")
        diagnostics.warn(f"{file_name} fila {row_number}: locker duplicado ignorado: {numero}.")
        return
    seen_lockers.add(numero_key)
    matricula = normalize_matricula(_cell(row, columns.get("locker_matricula")))
    empleado_id = repository.get_empleado_id(matricula) if matricula else None
    if matricula and empleado_id is None:
        diagnostics.inc("matrículas en lockers no encontradas")
        diagnostics.warn(f"{file_name} fila {row_number}: locker {numero} tiene matrícula no encontrada: {matricula}.")
    estado = normalize_estado_locker(_cell(row, columns.get("locker_estado")), bool(matricula))
    ubicacion = clean_text(_cell(row, columns.get("locker_ubicacion")))
    _, status = repository.upsert_locker(numero, estado, empleado_id, ubicacion)
    _count_status(diagnostics, "lockers", status)
    diagnostics.inc("filas lockers válidas")


def _import_estacionamiento_row(
    file_name: str,
    row_number: int,
    row: list[Any],
    columns: dict[str, int | None],
    repository: ImportacionRepository,
    diagnostics: ImportDiagnostics,
    seen_cajones: set[str],
) -> None:
    cajon = normalize_identifier(_cell(row, columns.get("parking_cajon")))
    if not cajon:
        return
    cajon_key = make_lookup_key(cajon)
    if cajon_key in seen_cajones:
        diagnostics.inc("duplicados ignorados")
        diagnostics.warn(f"{file_name} fila {row_number}: cajón duplicado ignorado: {cajon}.")
        return
    seen_cajones.add(cajon_key)
    matricula = normalize_matricula(_cell(row, columns.get("parking_matricula")))
    empleado_id = repository.get_empleado_id(matricula) if matricula else None
    if matricula and empleado_id is None:
        diagnostics.inc("matrículas en estacionamientos no encontradas")
        diagnostics.warn(f"{file_name} fila {row_number}: cajón {cajon} tiene matrícula no encontrada: {matricula}.")
    estado = normalize_estado_estacionamiento(_cell(row, columns.get("parking_estado")), bool(matricula))
    ubicacion = clean_text(_cell(row, columns.get("parking_ubicacion")))
    _, status = repository.upsert_estacionamiento(cajon, estado, empleado_id, ubicacion)
    _count_status(diagnostics, "estacionamientos", status)
    diagnostics.inc("filas estacionamientos válidas")


def _has_real_import_data(diagnostics: ImportDiagnostics) -> bool:
    real_keys = [
        "filas empleados válidas",
        "filas puestos válidas",
        "filas lockers válidas",
        "filas estacionamientos válidas",
        "objetos created",
        "objetos updated",
        "relaciones created",
        "relaciones updated",
    ]
    return any(diagnostics.counters.get(key, 0) > 0 for key in real_keys)


def _count_status(diagnostics: ImportDiagnostics, prefix: str, status: str) -> None:
    diagnostics.inc(f"{prefix} {status}")


def _cell(row: list[Any], index: int | None) -> Any:
    if index is None or index < 0 or index >= len(row):
        return None
    return row[index]


def _index_of(values: list[str], expected: str) -> int | None:
    try:
        return values.index(expected)
    except ValueError:
        return None


def _first_index_of(values: list[str], expected: str, start: int, end: int) -> int | None:
    for index in range(max(start, 0), min(end, len(values))):
        if values[index] == expected:
            return index
    return None


def _last_index_of(values: list[str], expected: str, start: int, end: int) -> int | None:
    for index in range(min(end, len(values)) - 1, max(start, 0) - 1, -1):
        if values[index] == expected:
            return index
    return None
