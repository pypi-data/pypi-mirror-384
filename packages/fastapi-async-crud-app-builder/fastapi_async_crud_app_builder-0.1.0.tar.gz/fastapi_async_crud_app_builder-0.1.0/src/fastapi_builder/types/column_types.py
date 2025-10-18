from enum import Enum
from typing import Dict, Any
class TypeKind(str, Enum):
    INTEGER = "integer"
    STRING = "string"
    TEXT = "text"
    BOOLEAN = "boolean"
    FLOAT = "float"
    DATETIME = "datetime"
    DATE = "date"
    JSON = "json"
    BYTES = "bytes"
    UUID = "uuid"
    ARRAY = "array"
    ENUM = "enum"
    UNKNOWN = "unknown"


_KIND_TO_PY: Dict[TypeKind, type] = {
    TypeKind.INTEGER: int,
    TypeKind.STRING: str,
    TypeKind.TEXT: str,
    TypeKind.BOOLEAN: bool,
    TypeKind.FLOAT: float,
    TypeKind.DATETIME: __import__("datetime").datetime,
    TypeKind.DATE: __import__("datetime").date,
    TypeKind.JSON: dict,
    TypeKind.BYTES: bytes,
    TypeKind.UUID: str,   # represent UUIDs as string in API
    TypeKind.ARRAY: list,
    TypeKind.ENUM: str,   # or a specific Enum class if you have one
    TypeKind.UNKNOWN: Any,
}

