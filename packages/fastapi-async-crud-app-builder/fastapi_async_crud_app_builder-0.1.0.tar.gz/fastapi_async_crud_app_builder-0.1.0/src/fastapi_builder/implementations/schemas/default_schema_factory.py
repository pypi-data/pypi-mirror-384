from typing import Optional, Type, Tuple, Dict, Any

from sqlmodel import SQLModel
from pydantic import BaseModel, create_model

from ...types.column_types import _KIND_TO_PY, TypeKind

from sqlalchemy import (
    Integer, String, Boolean, Float, DateTime, Date, LargeBinary, Enum as SAEnum
)
try:
    from sqlalchemy import JSON as SAJSON  # PG/Generic JSON
except Exception:
    SAJSON = None  # pragma: no cover

# Optional PG/MySQL specific helpers if available (we still handle via visit_name)
try:
    from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY as PGARRAY, JSONB as PGJSONB  # type: ignore
except Exception:
    PGUUID = PGARRAY = PGJSONB = None  # pragma: no cover

class DefaultSchemaFactory:
    """
    Builds Pydantic models (Query/Create/Update) with safe type inference.
    Uses TypeKind to classify SQLAlchemy types; maps to Python types for DTOs.
    """

    # ---------- public ----------
    def make_query(self, Model: Type[SQLModel]) -> Type[BaseModel]:
        fields: Dict[str, Tuple[type, Any]] = {}
        for c in Model.__table__.columns:
            kind = self._infer_kind(c.type)
            py = _KIND_TO_PY.get(kind, Any)
            fields[c.name] = (Optional[py], None)
        return create_model(f"Query{Model.__name__}", **fields)  # type: ignore

    def make_update(self, Model: Type[SQLModel]) -> Type[BaseModel]:
        fields: Dict[str, Tuple[type, Any]] = {}
        for c in Model.__table__.columns:
            if c.primary_key:
                continue
            kind = self._infer_kind(c.type)
            py = _KIND_TO_PY.get(kind, Any)
            fields[c.name] = (Optional[py], None)
        return create_model(f"Update{Model.__name__}", **fields)  # type: ignore

    def make_create(self, Model: Type[SQLModel], rls_col: Optional[str]) -> Type[BaseModel]:
        fields: Dict[str, Tuple[type, Any]] = {}
        for c in Model.__table__.columns:
            if c.primary_key:
                continue
            kind = self._infer_kind(c.type)
            py = _KIND_TO_PY.get(kind, Any)
            required = (not getattr(c, "nullable", True)) and (c.server_default is None) and (c.default is None)
            default = ... if (required and c.name != rls_col) else None
            fields[c.name] = (Optional[py], default)
        return create_model(f"Create{Model.__name__}", **fields)  # type: ignore

    # ---------- internals ----------
    def _infer_kind(self, satype: Any) -> TypeKind:
        """
        Return a TypeKind for a SQLAlchemy TypeEngine instance.
        Never raises; UNKNOWN on ambiguity.
        """
        # 1) Try native python_type (fast path)
        try:
            if hasattr(satype, "python_type"):
                pt = satype.python_type  # may raise NotImplementedError
                # Map common python types directly
                if pt is int: return TypeKind.INTEGER
                if pt is str: return TypeKind.STRING  # may also be TEXT; we discern below
                if pt is bool: return TypeKind.BOOLEAN
                if pt is float: return TypeKind.FLOAT
                from datetime import datetime, date
                if pt is datetime: return TypeKind.DATETIME
                if pt is date: return TypeKind.DATE
                if pt is bytes: return TypeKind.BYTES
        except NotImplementedError:
            pass
        except Exception:
            pass

        # 2) isinstance checks on SA classes
        try:
            if isinstance(satype, Integer): return TypeKind.INTEGER
            if isinstance(satype, String):  return TypeKind.STRING
            if isinstance(satype, Boolean): return TypeKind.BOOLEAN
            if isinstance(satype, Float):   return TypeKind.FLOAT
            if isinstance(satype, DateTime):return TypeKind.DATETIME
            if isinstance(satype, Date):    return TypeKind.DATE
            if isinstance(satype, LargeBinary): return TypeKind.BYTES
            if isinstance(satype, SAEnum):  return TypeKind.ENUM
            if SAJSON is not None and isinstance(satype, SAJSON): return TypeKind.JSON
            if PGUUID is not None and isinstance(satype, PGUUID): return TypeKind.UUID
            if PGARRAY is not None and isinstance(satype, PGARRAY): return TypeKind.ARRAY
            if PGJSONB is not None and isinstance(satype, PGJSONB): return TypeKind.JSON
        except Exception:
            pass

        # 3) Visit name heuristics (covers dialect-specific types)
        try:
            visit = getattr(satype, "__visit_name__", "").lower()
            # Distinguish text-ish from string
            if visit in {"text"}:
                return TypeKind.TEXT
            if "json" in visit:
                return TypeKind.JSON
            if "array" in visit:
                return TypeKind.ARRAY
            if "uuid" in visit:
                return TypeKind.UUID
            if visit in {"string", "varchar", "char", "nchar", "nvarchar"}:
                return TypeKind.STRING
            if visit in {"integer", "int", "smallint", "bigint"}:
                return TypeKind.INTEGER
            if visit in {"boolean", "bool"}:
                return TypeKind.BOOLEAN
            if visit in {"float", "double", "real", "numeric", "decimal"}:
                return TypeKind.FLOAT
            if visit in {"datetime", "timestamp", "timestamptz"}:
                return TypeKind.DATETIME
            if visit in {"date"}:
                return TypeKind.DATE
            if visit in {"large_binary", "blob", "bytea"}:
                return TypeKind.BYTES
            if visit in {"enum"}:
                return TypeKind.ENUM
        except Exception:
            pass

        # 4) Unknown / custom → treat as string in UI *or* Any for DTO.
        return TypeKind.UNKNOWN
