# simple_config_parser.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Type
from datetime import datetime, date
import uuid

from ..auth_builder import JWTConfig
from ...types import AppConfig

from pydantic import BaseModel
from sqlalchemy import Column, DateTime as SADateTime, func
from sqlalchemy import String as SAString, Text as SAText, Integer as SAInteger
from sqlalchemy import Boolean as SABoolean, Float as SAFloat, LargeBinary as SALargeBinary, Date as SADate
from sqlalchemy.dialects.sqlite import JSON as SAJSON  # works on sqlite; for PG you'd use sqlalchemy.JSON
from sqlmodel import SQLModel, Field

class SimpleConfigParser:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg

    def build(self) -> Tuple[
        Dict[str, Type[SQLModel]],
        Optional[Type[SQLModel]],
        AppConfig,
        Dict[str, Any],
    ]:
        # ---- app config ----
        app_cfg = self.cfg.get("app", {}) or {}
        slug = app_cfg.get("slug") or "app"
        rls_col = app_cfg.get("rls_column_name")
        timestamps = bool(app_cfg.get("timestamps", True))
        soft_delete = bool(app_cfg.get("soft_delete", False))
        app_config = AppConfig(slug=slug, rls_column_name=rls_col)

        # ---- auth (optional) ----
        user_model_cls: Optional[Type[SQLModel]] = None
        auth_kwargs: Dict[str, Any] = {}
        auth_cfg = self.cfg.get("auth")
        if auth_cfg:
            ucfg = auth_cfg["user_model"]
            user_model_cls = self._make_sqlmodel_class(
                name=ucfg["name"],
                table_name=ucfg.get("table_name") or ucfg["name"].lower(),
                fields=ucfg["fields"],
                rls_col=None,                   # no RLS on user table
                timestamps=timestamps,
                soft_delete=soft_delete,
            )
            auth_kwargs = {
                "user_model": user_model_cls,
                "identification_attr": ucfg["identifier_field"],
                "password_attr": ucfg["password_field"],
                "is_active_attr": ucfg.get("is_active_field"),
                "jwt_config": JWTConfig(**auth_cfg["jwt"]),
                "token_url": "/auth/login",
            }

        # ---- app models ----
        models: Dict[str, Type[SQLModel]] = {}
        for m in self.cfg.get("models", []):
            Model = self._make_sqlmodel_class(
                name=m["name"],
                table_name=m.get("table_name") or m["name"].lower(),
                fields=m["fields"],
                rls_col=rls_col,
                timestamps=timestamps,
                soft_delete=soft_delete,
            )
            models[m["name"].lower()] = Model

        return models, user_model_cls, app_config, auth_kwargs

    # ---------- internals ----------
    def _make_sqlmodel_class(
        self,
        *,
        name: str,
        table_name: str,
        fields: List[Dict[str, Any]],
        rls_col: Optional[str],
        timestamps: bool,
        soft_delete: bool,
    ) -> Type[SQLModel]:
        """
        Build a SQLModel class with optional RLS column, timestamps, and soft-delete.
        We set __annotations__ so OpenAPI is nice and Pydantic validation works as expected.
        """
        namespace: Dict[str, Any] = {"__tablename__": table_name}
        annotations: Dict[str, Any] = {}

        # Track what’s already defined
        has_created = any(f["name"] == "created_at" for f in fields)
        has_updated = any(f["name"] == "updated_at" for f in fields)
        has_deleted = any(f["name"] == "is_deleted" for f in fields)
        has_rls = bool(rls_col) and any(f["name"] == rls_col for f in fields)
        # Inject user-defined fields
        for f in fields:
            fname = f["name"]
            py_type, field_obj = self._field_from_spec(f)
            annotations[fname] = self._optionalize_type(py_type, f)
            namespace[fname] = field_obj

        # Auto RLS column if configured & missing
        if rls_col and not has_rls:
            annotations[rls_col] = Optional[int]  # common choice; can be any type you prefer
            namespace[rls_col] = Field(default=None, nullable=True, index=True)

        # Auto timestamps
        if timestamps and not has_created:
            annotations["created_at"] = datetime
            namespace["created_at"] = Field(
                default_factory=datetime.utcnow,
                nullable=False
            )
        if timestamps and not has_updated:
            annotations["updated_at"] = datetime
            namespace["updated_at"] = Field(
                default_factory=datetime.utcnow,
                nullable=False
            )

        # Auto soft delete
        if soft_delete and not has_deleted:
            annotations["is_deleted"] = bool
            namespace["is_deleted"] = Field(default=False, nullable=False, index=True)

        namespace["__annotations__"] = annotations
        cls = type(name, (SQLModel,), namespace, table = True)
        return cls

    def _optionalize_type(self, py_type: type, spec: Dict[str, Any]):
        """
        Make type Optional[...] when field is nullable or has a default/not required.
        """
        nullable = spec.get("nullable", True)
        primary_key = bool(spec.get("primary_key", False))
        has_default = "default" in spec
        # PKs are often Optional for create payloads; keep Optional for ergonomic DTOs
        if nullable or has_default or primary_key:
            from typing import Optional as TypingOptional
            return TypingOptional[py_type]
        return py_type

    def _field_from_spec(self, spec: Dict[str, Any]) -> Tuple[type, Any]:
        """
        Map config field -> (python type, SQLModel Field(...))
        Supports:
        primary_key | nullable | default | indexed | unique | foreign_key
        type in {integer,string,text,boolean,float,datetime,date,uuid,json,bytes}
        """
        name = spec["name"]
        kind = (spec.get("type") or "string").lower()
        primary_key = bool(spec.get("primary_key", False))
        nullable = spec.get("nullable", True)
        default = spec.get("default", None)
        indexed = bool(spec.get("indexed", False))
        unique = bool(spec.get("unique", False))
        foreign_key = spec.get("foreign_key")

        py_type, sa_type = self._py_and_sa_type(kind)

        # Defaults
        field_kwargs: Dict[str, Any] = {}
        
        if default is not None:
            field_kwargs["default"] = default

        if primary_key:
            field_kwargs['primary_key'] = primary_key
            field_kwargs['nullable'] = True

        if nullable == True or nullable is not None:
            field_kwargs['nullable'] = True

        if foreign_key:
            field_kwargs['foreign_key'] = foreign_key

        if indexed:
            field_kwargs['index'] = indexed

        sa_col = None
        
        if primary_key or indexed or nullable or (foreign_key or foreign_key is not None):
            return py_type, Field(**field_kwargs)
        elif sa_type is not None:
            sa_col = Column(sa_type, unique=unique)

            field = Field(sa_column=sa_col)
        return py_type, field
    
    def _py_and_sa_type(self, kind: str) -> Tuple[type, Optional[Any]]:
        k = kind.lower()
        if k == "integer":
            return int, SAInteger
        if k == "string":
            return str, SAString
        if k == "text":
            return str, SAText
        if k == "boolean":
            return bool, SABoolean
        if k == "float":
            return float, SAFloat
        if k == "datetime":
            return datetime, SADateTime(timezone=True)
        if k == "date":
            return date, SADate
        if k == "uuid":
            # store as string (portable), validate as uuid.UUID in higher layer if needed
            return uuid.UUID, SAString(36)
        if k == "json":
            return dict, SAJSON
        if k == "bytes":
            return bytes, SALargeBinary
        # fallback
        return str, SAString
