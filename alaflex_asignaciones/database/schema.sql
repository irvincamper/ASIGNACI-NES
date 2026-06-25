PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS puestos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    clave TEXT,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empleados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    id_puesto INTEGER NOT NULL,
    turno TEXT NOT NULL,
    fecha_ingreso TEXT NOT NULL,
    fecha_baja TEXT,
    estado TEXT NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_puesto) REFERENCES puestos(id)
);

CREATE TABLE IF NOT EXISTS objetos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    stock_total INTEGER NOT NULL DEFAULT 0 CHECK (stock_total >= 0),
    stock_disponible INTEGER NOT NULL DEFAULT 0 CHECK (stock_disponible >= 0),
    requiere_devolucion INTEGER NOT NULL CHECK (requiere_devolucion IN (0, 1)),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (stock_disponible <= stock_total)
);

CREATE TABLE IF NOT EXISTS reglas_por_puesto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_puesto INTEGER NOT NULL,
    id_objeto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    obligatorio INTEGER NOT NULL DEFAULT 1 CHECK (obligatorio IN (0, 1)),
    requiere_devolucion INTEGER NOT NULL DEFAULT 1 CHECK (requiere_devolucion IN (0, 1)),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_puesto, id_objeto),
    FOREIGN KEY (id_puesto) REFERENCES puestos(id),
    FOREIGN KEY (id_objeto) REFERENCES objetos(id)
);

CREATE TABLE IF NOT EXISTS asignaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL,
    id_objeto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    tipo_movimiento TEXT NOT NULL DEFAULT 'Asignación inicial',
    estado TEXT NOT NULL CHECK (estado IN ('Pendiente', 'Asignado', 'Devuelto', 'No aplica', 'Pendiente de devolución')),
    fecha_asignacion TEXT,
    fecha_devolucion TEXT,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id),
    FOREIGN KEY (id_objeto) REFERENCES objetos(id)
);

CREATE TABLE IF NOT EXISTS estacionamientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cajon TEXT NOT NULL UNIQUE,
    estado TEXT NOT NULL DEFAULT 'Libre' CHECK (estado IN ('Libre', 'Ocupado', 'Conflicto')),
    id_empleado INTEGER,
    tipo_asignacion TEXT,
    ubicacion TEXT,
    turno_compartido INTEGER NOT NULL DEFAULT 0 CHECK (turno_compartido IN (0, 1)),
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS lockers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    estado TEXT NOT NULL DEFAULT 'Libre' CHECK (estado IN ('Libre', 'Ocupado')),
    id_empleado INTEGER,
    ubicacion TEXT,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS historial_cambios_puesto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL,
    puesto_anterior TEXT NOT NULL,
    puesto_nuevo TEXT NOT NULL,
    fecha_cambio TEXT NOT NULL,
    motivo TEXT,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS historial_bajas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL,
    fecha_baja TEXT NOT NULL,
    motivo_baja TEXT NOT NULL,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS historial_estacionamientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER,
    cajon_anterior TEXT,
    cajon_nuevo TEXT,
    fecha_movimiento TEXT NOT NULL,
    tipo_movimiento TEXT NOT NULL,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS expedientes_digitales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL,
    matricula TEXT NOT NULL,
    motivo TEXT NOT NULL,
    ruta_pdf TEXT,
    fecha_generacion TEXT,
    total_recursos INTEGER NOT NULL DEFAULT 0,
    paginas INTEGER NOT NULL DEFAULT 0,
    revision TEXT,
    estado TEXT NOT NULL DEFAULT 'Generado',
    json_snapshot TEXT,
    json_congelado TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id)
);

CREATE TABLE IF NOT EXISTS expediente_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_expediente INTEGER NOT NULL,
    concepto TEXT NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    estado TEXT,
    observaciones TEXT,
    FOREIGN KEY (id_expediente) REFERENCES expedientes_digitales(id)
);

CREATE TABLE IF NOT EXISTS movimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    id_empleado INTEGER,
    id_objeto INTEGER,
    id_asignacion INTEGER,
    estado_anterior TEXT,
    estado_nuevo TEXT,
    observacion TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empleado) REFERENCES empleados(id)
);
