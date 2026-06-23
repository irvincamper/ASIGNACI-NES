from __future__ import annotations


def require_text(value: str, message: str) -> str | None:
    return None if value and value.strip() else message


def validate_matricula_required(value: str) -> str | None:
    return require_text(value, "Debe ingresar una matrícula.")


def validate_nombre_required(value: str) -> str | None:
    return require_text(value, "Debe ingresar el nombre completo.")


def validate_puesto_required(value: str) -> str | None:
    return require_text(value, "Debe seleccionar un puesto antes de guardar el empleado.")


def validate_turno_required(value: str) -> str | None:
    return require_text(value, "Debe seleccionar un turno antes de guardar el empleado.")


def validate_fecha_ingreso_required(value: str) -> str | None:
    return require_text(value, "Debe ingresar la fecha de ingreso.")


def validate_stock(stock_total: int, stock_disponible: int) -> str | None:
    if stock_total < 0 or stock_disponible < 0:
        return "El stock no puede ser negativo."
    if stock_disponible > stock_total:
        return "El stock disponible no puede ser mayor que el stock total."
    return None


def validate_cantidad(cantidad: int) -> str | None:
    return None if cantidad > 0 else "La cantidad debe ser mayor a cero."


def duplicate_matricula_message() -> str:
    return "La matrícula ya existe. No se puede registrar otro empleado con la misma matrícula."


def duplicate_relacion_message() -> str:
    return "Ya existe una relación entre el puesto y el objeto seleccionado."


def matricula_inexistente_message() -> str:
    return "La matrícula ingresada no existe en empleados activos."
