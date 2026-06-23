from __future__ import annotations

import sqlite3
from pathlib import Path

from utils.constants import DATA_DIR, FUTURE_DATABASE_PATH, PROJECT_ROOT

SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def get_database_path() -> Path:
    return FUTURE_DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(FUTURE_DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def apply_safe_migrations(connection: sqlite3.Connection) -> None:
    migrations = [
        ("puestos", "clave", "ALTER TABLE puestos ADD COLUMN clave TEXT"),
        ("estacionamientos", "ubicacion", "ALTER TABLE estacionamientos ADD COLUMN ubicacion TEXT"),
        ("lockers", "ubicacion", "ALTER TABLE lockers ADD COLUMN ubicacion TEXT"),
    ]
    for table, column, statement in migrations:
        if not _column_exists(connection, table, column):
            connection.execute(statement)


def init_database() -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        with get_connection() as connection:
            connection.executescript(schema)
            apply_safe_migrations(connection)
            from database.seed import seed_database

            seed_database(connection)
            connection.commit()
    except sqlite3.Error as exc:
        print(f"[ALAFLEX][SQLite] Error al inicializar la base de datos: {exc}")
    except OSError as exc:
        print(f"[ALAFLEX][SQLite] No se pudo preparar la base de datos: {exc}")
