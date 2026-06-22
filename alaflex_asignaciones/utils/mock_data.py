from __future__ import annotations

DASHBOARD_KPIS = [
    {"title": "Empleados activos", "value": "162", "icon": "fa5s.users", "color": "#0057E7"},
    {"title": "Objetos asignados", "value": "1634", "icon": "fa5s.cube", "color": "#16A05D"},
    {"title": "Pendientes", "value": "1634", "icon": "fa5s.clock", "color": "#F59E0B"},
    {"title": "Estacionamientos libres", "value": "5", "icon": "fa5s.parking", "color": "#0057E7"},
    {"title": "Estacionamientos ocupados", "value": "15", "icon": "fa5s.car", "color": "#7C3AED"},
    {"title": "Conflictos", "value": "0", "icon": "fa5s.exclamation-triangle", "color": "#E11D48"},
]

DASHBOARD_ALERTS = [
    {"text": "Conflictos de estacionamiento por mismo turno.", "value": "0", "icon": "fa5s.exclamation-triangle", "color": "#E11D48"},
    {"text": "Asignaciones pendientes de validación inicial.", "value": "1634", "icon": "fa5s.clock", "color": "#F59E0B"},
    {"text": "Estacionamientos compartidos por turno.", "value": "2", "icon": "fa5s.users", "color": "#0057E7"},
    {"text": "Lockers ocupados actualmente.", "value": "134", "icon": "fa5s.archive", "color": "#7C3AED"},
]

EMPLEADOS = [
    {"matricula": "A00123", "nombre": "Juan Carlos Martínez", "puesto": "Analista de Sistemas", "estado": "Activo", "objetos": 8, "estacionamiento": "E-12", "pendientes": 2},
    {"matricula": "A00245", "nombre": "María Fernanda López", "puesto": "Coordinador de Operaciones", "estado": "Activo", "objetos": 12, "estacionamiento": "B-07", "pendientes": 1},
    {"matricula": "A00367", "nombre": "Luis Alberto Ramírez", "puesto": "Técnico de Mantenimiento", "estado": "Activo", "objetos": 6, "estacionamiento": "D-15", "pendientes": 0},
    {"matricula": "A00489", "nombre": "Ana Sofía Herrera", "puesto": "Recursos Humanos", "estado": "Activo", "objetos": 5, "estacionamiento": "A-03", "pendientes": 3},
    {"matricula": "A00556", "nombre": "Roberto Sánchez Vega", "puesto": "Supervisor de Almacén", "estado": "Activo", "objetos": 9, "estacionamiento": "C-21", "pendientes": 1},
    {"matricula": "A00678", "nombre": "Laura Gabriela Torres", "puesto": "Analista Financiero", "estado": "Inactivo", "objetos": 3, "estacionamiento": "-", "pendientes": 4},
    {"matricula": "A00791", "nombre": "Carlos Eduardo Nájera", "puesto": "Desarrollador de Software", "estado": "Activo", "objetos": 10, "estacionamiento": "E-08", "pendientes": 0},
    {"matricula": "A00834", "nombre": "Jazmín Guadalupe Ruiz", "puesto": "Asistente Administrativo", "estado": "Activo", "objetos": 4, "estacionamiento": "A-11", "pendientes": 2},
]

OBJETOS_KPIS = [
    {"title": "Total objetos", "value": "258", "icon": "fa5s.cube", "color": "#0057E7"},
    {"title": "Stock bajo", "value": "18", "icon": "fa5s.exclamation-triangle", "color": "#F59E0B"},
    {"title": "Activos", "value": "240", "icon": "fa5s.check-circle", "color": "#16A05D"},
]

OBJETOS = [
    {"nombre": "Casco de seguridad", "nombre_icon": "fa5s.hard-hat", "categoria": "Seguridad", "stock": 45, "requiere": "Sí", "estado": "Activo"},
    {"nombre": "Lentes de seguridad", "nombre_icon": "fa5s.glasses", "categoria": "Seguridad", "stock": 32, "requiere": "Sí", "estado": "Activo"},
    {"nombre": "Uniforme corporativo", "nombre_icon": "fa5s.tshirt", "categoria": "Vestimenta", "stock": 78, "requiere": "Sí", "estado": "Activo"},
    {"nombre": "Laptop corporativa", "nombre_icon": "fa5s.laptop", "categoria": "Tecnología", "stock": 26, "requiere": "Sí", "estado": "Activo"},
    {"nombre": "Tarjeta de acceso", "nombre_icon": "fa5s.id-card", "categoria": "Acceso", "stock": 120, "requiere": "No", "estado": "Activo"},
    {"nombre": "Protector auditivo", "nombre_icon": "fa5s.headphones", "categoria": "Seguridad", "stock": 22, "requiere": "Sí", "estado": "Activo"},
    {"nombre": "Guantes de trabajo", "nombre_icon": "fa5s.mitten", "categoria": "Seguridad", "stock": 60, "requiere": "Sí", "estado": "Activo"},
    {"nombre": "Mochila corporativa", "nombre_icon": "fa5s.briefcase", "categoria": "Accesorios", "stock": 35, "requiere": "Sí", "estado": "Activo"},
]

RELACIONES_KPIS = [
    {"title": "Total relaciones", "value": "156", "icon": "fa5s.link", "color": "#0057E7"},
    {"title": "Obligatorias", "value": "112", "icon": "fa5s.shield-alt", "color": "#16A05D"},
    {"title": "Con devolución", "value": "44", "icon": "fa5s.sync-alt", "color": "#F59E0B"},
]

RELACIONES = [
    {"puesto": "Operador de Montacargas", "objeto": "Casco de seguridad", "cantidad": 1, "obligatorio": "Sí", "devolucion": "Sí", "estado": "Activo"},
    {"puesto": "Operador de Montacargas", "objeto": "Chaleco reflectante", "cantidad": 1, "obligatorio": "Sí", "devolucion": "Sí", "estado": "Activo"},
    {"puesto": "Supervisor de Almacén", "objeto": "Radio portátil", "cantidad": 1, "obligatorio": "Sí", "devolucion": "Sí", "estado": "Activo"},
    {"puesto": "Supervisor de Almacén", "objeto": "Tablet corporativa", "cantidad": 1, "obligatorio": "Sí", "devolucion": "Sí", "estado": "Activo"},
    {"puesto": "Auxiliar de Almacén", "objeto": "Guantes de trabajo", "cantidad": 2, "obligatorio": "No", "devolucion": "Sí", "estado": "Activo"},
    {"puesto": "Auxiliar de Almacén", "objeto": "Lentes de seguridad", "cantidad": 1, "obligatorio": "No", "devolucion": "Sí", "estado": "Activo"},
    {"puesto": "Conductor", "objeto": "Extintor vehicular", "cantidad": 1, "obligatorio": "Sí", "devolucion": "No", "estado": "Activo"},
    {"puesto": "Conductor", "objeto": "Botiquín de primeros auxilios", "cantidad": 1, "obligatorio": "Sí", "devolucion": "No", "estado": "Activo"},
]

PUESTOS = [
    "Seleccionar puesto",
    "Operador de Montacargas",
    "Supervisor de Almacén",
    "Auxiliar de Almacén",
    "Conductor",
    "Analista de Sistemas",
]

ESTACIONAMIENTOS_KPIS = [
    {"title": "Totales", "value": "245", "icon": "fa5s.parking", "color": "#0057E7"},
    {"title": "Libres", "value": "128", "icon": "fa5s.parking", "color": "#16A05D"},
    {"title": "Ocupados", "value": "112", "icon": "fa5s.car", "color": "#7C3AED"},
    {"title": "Conflictos", "value": "5", "icon": "fa5s.exclamation-triangle", "color": "#E11D48"},
]

ESTACIONAMIENTOS = [
    {"cajon": "A-001", "estado": "Ocupado", "matricula": "ABC-1234", "empleado": "Juan Pérez", "tipo": "Asignación fija"},
    {"cajon": "A-002", "estado": "Libre", "matricula": "-", "empleado": "-", "tipo": "-"},
    {"cajon": "A-003", "estado": "Ocupado", "matricula": "XYZ-5678", "empleado": "María López", "tipo": "Asignación fija"},
    {"cajon": "A-004", "estado": "Conflicto", "matricula": "DEF-9012", "empleado": "Carlos Ramírez", "tipo": "Asignación manual"},
    {"cajon": "B-001", "estado": "Libre", "matricula": "-", "empleado": "-", "tipo": "-"},
    {"cajon": "B-002", "estado": "Ocupado", "matricula": "GHI-3456", "empleado": "Ana Torres", "tipo": "Asignación fija"},
    {"cajon": "B-003", "estado": "Libre", "matricula": "-", "empleado": "-", "tipo": "-"},
    {"cajon": "B-004", "estado": "Conflicto", "matricula": "JKL-7890", "empleado": "Luis Hernández", "tipo": "Asignación manual"},
]

PDF_PREVIEW = {
    "matricula": "667",
    "nombre": "BRYAM ALBERTO MANZUR MIMILA",
    "motivo": "Cambio de puesto",
    "puesto": "STU - Supervisor de Turno",
    "puesto_anterior": "ACA - Auditor de Calidad - Proceso",
    "fecha": "20/04/2028",
    "total_recursos": "14",
    "paginas": "2",
    "ruta": "C:\\Reportes\\ALAFLEX\\ALA-RH-FR-29_667.pdf",
    "formato": "PDF",
    "reporte": "ALA-RH-FR-29",
    "revision": "2",
}

PDF_RECURSOS = [
    {"no": "1", "tipo": "X", "fecha": "", "categoria": "Equipo", "descripcion": "Radio transmisor", "cantidad": "", "unidad": "", "firma": ""},
    {"no": "2", "tipo": "X", "fecha": "", "categoria": "Equipo", "descripcion": "Teléfono", "cantidad": "", "unidad": "", "firma": ""},
    {"no": "3", "tipo": "X", "fecha": "", "categoria": "Herramienta", "descripcion": "Llavero allen 1.5-6.0 mm", "cantidad": "", "unidad": "", "firma": ""},
    {"no": "4", "tipo": "X", "fecha": "", "categoria": "Herramienta", "descripcion": "Navaja fina", "cantidad": "", "unidad": "", "firma": ""},
    {"no": "5", "tipo": "X", "fecha": "", "categoria": "Herramienta", "descripcion": "Navaja gruesa", "cantidad": "", "unidad": "", "firma": ""},
    {"no": "6", "tipo": "X", "fecha": "", "categoria": "EPP", "descripcion": "Casco de seguridad", "cantidad": "", "unidad": "", "firma": ""},
    {"no": "7", "tipo": "X", "fecha": "", "categoria": "EPP", "descripcion": "Suspensión de casco de seguridad", "cantidad": "", "unidad": "", "firma": ""},
]
