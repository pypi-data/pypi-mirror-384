from typing import Type, Optional, Any, Dict
from sqlmodel import SQLModel

from ...types import UserIdExtractor

from fastapi import HTTPException

class OwnerColumnRLS:
    """RLS that uses a single owner column (e.g. 'owner_id')."""
    def __init__(self, user_id_extractor: UserIdExtractor, rls_column_name: Optional[str]):
        self._uid = user_id_extractor
        self._col = rls_column_name

    def _rls_col(self, Model: Type[SQLModel]) -> Optional[str]:
        if not self._col:
            return None
        return self._col if self._col in Model.__table__.c else None

    def condition(self, Model: Type[SQLModel], user: Any):
        col = self._rls_col(Model)
        if not col:
            return None
        uid = self._uid(user)
        if uid is None:
            raise HTTPException(401, "Unauthorized")
        return Model.__table__.c[col] == uid

    def inject_on_create(self, Model: Type[SQLModel], data: Dict[str, Any], user: Any) -> None:
        col = self._rls_col(Model)
        if not col:
            return
        uid = self._uid(user)
        if uid is None:
            raise HTTPException(401, "Unauthorized")
        data[col] = uid

    def guard_update(self, Model: Type[SQLModel], db_obj: Any, changes: Dict[str, Any], user: Any) -> None:
        col = self._rls_col(Model)
        if not col or col not in changes:
            return
        # force it back to current user (or raise 403 if you prefer)
        uid = self._uid(user)
        if uid is None:
            raise HTTPException(401, "Unauthorized")
        changes[col] = uid
