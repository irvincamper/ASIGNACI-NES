from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


_SPACE_RE = re.compile(r"\s+")
_NON_KEY_RE = re.compile(r"[^A-Z0-9]+")
_NON_HEADER_RE = re.compile(r"[^a-z0-9]+")


def remove_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def clean_text(value: Any, uppercase: bool = False) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        text = value.strftime("%Y-%m-%d")
    elif isinstance(value, date):
        text = value.isoformat()
    else:
        text = str(value)
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = _SPACE_RE.sub(" ", text).strip()
    return text.upper() if uppercase else text


def normalize_header(value: Any) -> str:
    text = remove_accents(clean_text(value).lower())
    text = _NON_HEADER_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def make_lookup_key(value: Any) -> str:
    text = remove_accents(clean_text(value, uppercase=True))
    text = _NON_KEY_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def normalize_matricula(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value).strip()
    text = clean_text(value)
    if not text:
        return ""
    try:
        decimal_value = Decimal(text)
        if decimal_value == decimal_value.to_integral_value():
            return str(int(decimal_value))
    except (InvalidOperation, ValueError):
        pass
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def normalize_identifier(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else clean_text(value)
    text = clean_text(value)
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def normalize_turno(value: Any) -> str:
    text = clean_text(value)
    return text if text else "Pendiente de revisión"


def normalize_estado_estacionamiento(value: Any, has_employee: bool = False) -> str:
    key = make_lookup_key(value)
    if "CONFLICT" in key:
        return "Conflicto"
    if "OCUP" in key or "ASIGN" in key:
        return "Ocupado"
    if "LIBRE" in key or "DISPON" in key:
        return "Libre"
    return "Ocupado" if has_employee else "Libre"


def normalize_estado_locker(value: Any, has_employee: bool = False) -> str:
    key = make_lookup_key(value)
    if "OCUP" in key or "ASIGN" in key:
        return "Ocupado"
    if "LIBRE" in key or "DISPON" in key:
        return "Libre"
    return "Ocupado" if has_employee else "Libre"


def marked_as_assigned(value: Any) -> bool:
    key = make_lookup_key(value)
    return key in {"X", "SI", "S", "1", "TRUE"} or value == 1


def default_requires_return(category: str) -> int:
    key = make_lookup_key(category)
    if key in {"PAPELERIA", "OTROS", "OTRO"}:
        return 0
    return 1
