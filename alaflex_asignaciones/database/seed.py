from __future__ import annotations

import sqlite3


def _table_empty(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
    return int(row["total"]) == 0


def _ids_by_name(connection: sqlite3.Connection, table: str, field: str = "nombre") -> dict[str, int]:
    rows = connection.execute(f"SELECT id, {field} FROM {table}").fetchall()
    return {row[field]: int(row["id"]) for row in rows}


def seed_database(connection: sqlite3.Connection) -> None:
    from services.importacion_service import importar_datos_iniciales_desde_importar

    import_result = importar_datos_iniciales_desde_importar(connection)
    if import_result.imported_real_data:
        return

    seed_puestos(connection)
    seed_objetos(connection)
    seed_empleados(connection)
    seed_estacionamientos(connection)
    seed_lockers(connection)
    seed_reglas(connection)
    seed_asignaciones(connection)


def seed_puestos(connection: sqlite3.Connection) -> None:
    if not _table_empty(connection, "puestos"):
        return
    puestos = [
        "ALMACENISTA DE PRODUCTO TERMINADO",
        "TECNICO EN MANTENIMIENTO DE HERRAMENTALES",
        "OPERADOR",
        "SUPERVISOR",
        "ADMINISTRATIVO",
    ]
    connection.executemany("INSERT INTO puestos (nombre) VALUES (?)", [(puesto,) for puesto in puestos])


def seed_objetos(connection: sqlite3.Connection) -> None:
    if not _table_empty(connection, "objetos"):
        return
    objetos = [
        ("Casco", "Seguridad", 1),
        ("Chaleco", "Vestimenta", 1),
        ("Lentes de seguridad", "Seguridad", 1),
        ("Guantes", "Seguridad", 1),
        ("Gafete", "Acceso", 0),
        ("Uniforme", "Vestimenta", 1),
        ("Botas", "Seguridad", 1),
        ("Locker", "Accesorios", 1),
    ]
    connection.executemany(
        """
        INSERT INTO objetos (nombre, categoria, requiere_devolucion)
        VALUES (?, ?, ?)
        """,
        objetos,
    )


def seed_empleados(connection: sqlite3.Connection) -> None:
    if not _table_empty(connection, "empleados"):
        return
    puestos = _ids_by_name(connection, "puestos")
    empleados = [
        ("1001", "Juan Pérez López", puestos["ALMACENISTA DE PRODUCTO TERMINADO"], "A", "2026-01-08", "Activo", ""),
        ("1002", "María González Ruiz", puestos["TECNICO EN MANTENIMIENTO DE HERRAMENTALES"], "B", "2026-01-12", "Activo", ""),
        ("1003", "Carlos Hernández Soto", puestos["OPERADOR"], "C", "2026-02-03", "Activo", ""),
        ("1004", "Ana Martínez Flores", puestos["ADMINISTRATIVO"], "A", "2026-02-18", "Activo", ""),
    ]
    connection.executemany(
        """
        INSERT INTO empleados (matricula, nombre, id_puesto, turno, fecha_ingreso, estado, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        empleados,
    )


def seed_estacionamientos(connection: sqlite3.Connection) -> None:
    if not _table_empty(connection, "estacionamientos"):
        return
    empleados = _ids_by_name(connection, "empleados", "matricula")
    estacionamientos = [
        ("A-01", "Ocupado", empleados["1001"], "Asignación fija", 0, ""),
        ("A-02", "Libre", None, None, 0, ""),
        ("A-03", "Ocupado", empleados["1002"], "Asignación fija", 0, ""),
        ("A-04", "Conflicto", empleados["1003"], "Asignación manual", 1, "Revisar posible cruce de turno."),
        ("A-05", "Libre", None, None, 0, ""),
    ]
    connection.executemany(
        """
        INSERT INTO estacionamientos (cajon, estado, id_empleado, tipo_asignacion, turno_compartido, observaciones)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        estacionamientos,
    )


def seed_lockers(connection: sqlite3.Connection) -> None:
    if not _table_empty(connection, "lockers"):
        return
    empleados = _ids_by_name(connection, "empleados", "matricula")
    lockers = [
        ("L-001", "Ocupado", empleados["1001"], ""),
        ("L-002", "Libre", None, ""),
        ("L-003", "Ocupado", empleados["1002"], ""),
        ("L-004", "Libre", None, ""),
    ]
    connection.executemany(
        "INSERT INTO lockers (numero, estado, id_empleado, observaciones) VALUES (?, ?, ?, ?)",
        lockers,
    )


def seed_reglas(connection: sqlite3.Connection) -> None:
    if not _table_empty(connection, "reglas_por_puesto"):
        return
    puestos = _ids_by_name(connection, "puestos")
    objetos = _ids_by_name(connection, "objetos")
    reglas = [
        ("ALMACENISTA DE PRODUCTO TERMINADO", "Casco", 1, 1, 1),
        ("ALMACENISTA DE PRODUCTO TERMINADO", "Chaleco", 1, 1, 1),
        ("ALMACENISTA DE PRODUCTO TERMINADO", "Guantes", 2, 1, 1),
        ("ALMACENISTA DE PRODUCTO TERMINADO", "Botas", 1, 1, 1),
        ("TECNICO EN MANTENIMIENTO DE HERRAMENTALES", "Casco", 1, 1, 1),
        ("TECNICO EN MANTENIMIENTO DE HERRAMENTALES", "Lentes de seguridad", 1, 1, 1),
        ("TECNICO EN MANTENIMIENTO DE HERRAMENTALES", "Guantes", 2, 1, 1),
        ("TECNICO EN MANTENIMIENTO DE HERRAMENTALES", "Botas", 1, 1, 1),
        ("ADMINISTRATIVO", "Gafete", 1, 1, 0),
    ]
    connection.executemany(
        """
        INSERT INTO reglas_por_puesto (id_puesto, id_objeto, cantidad, obligatorio, requiere_devolucion)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(puestos[puesto], objetos[objeto], cantidad, obligatorio, devolucion) for puesto, objeto, cantidad, obligatorio, devolucion in reglas],
    )


def seed_asignaciones(connection: sqlite3.Connection) -> None:
    if not _table_empty(connection, "asignaciones"):
        return
    empleados = _ids_by_name(connection, "empleados", "matricula")
    objetos = _ids_by_name(connection, "objetos")
    asignaciones = [
        (empleados["1001"], objetos["Casco"], 1, "Asignación inicial", "Asignado", "2026-01-08", None, ""),
        (empleados["1001"], objetos["Chaleco"], 1, "Asignación inicial", "Pendiente", None, None, ""),
        (empleados["1001"], objetos["Guantes"], 2, "Asignación inicial", "Pendiente de devolución", "2026-01-08", None, ""),
        (empleados["1002"], objetos["Casco"], 1, "Asignación inicial", "Asignado", "2026-01-12", None, ""),
        (empleados["1002"], objetos["Lentes de seguridad"], 1, "Asignación inicial", "Pendiente", None, None, ""),
        (empleados["1003"], objetos["Gafete"], 1, "Asignación inicial", "Devuelto", "2026-02-03", "2026-03-01", ""),
        (empleados["1004"], objetos["Gafete"], 1, "Asignación inicial", "Asignado", "2026-02-18", None, ""),
    ]
    connection.executemany(
        """
        INSERT INTO asignaciones
            (id_empleado, id_objeto, cantidad, tipo_movimiento, estado, fecha_asignacion, fecha_devolucion, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        asignaciones,
    )
