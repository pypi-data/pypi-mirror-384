from typing import Type, Dict, Any, Optional

from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

class SqlModelAsyncBackend:
    """Default CRUD that talks directly to the database with SQLModel/AsyncSession."""
    def _pk_name(self, Model: Type[SQLModel]) -> str:
        for c in Model.__table__.columns:
            if c.primary_key:
                return c.name
        raise RuntimeError(f"{Model.__name__} has no primary key")

    async def list(
        self, session: AsyncSession, Model: Type[SQLModel],
        filters: Dict[str, Any], limit: int, offset: int, rls_cond: Any
    ) -> list[Any]:
        stmt = select(Model)
        if rls_cond is not None:
            stmt = stmt.where(rls_cond)
        for k, v in filters.items():
            if k in Model.__table__.c and v is not None:
                stmt = stmt.where(Model.__table__.c[k] == v)
        stmt = stmt.offset(offset).limit(limit)
        res = await session.exec(stmt)
        return res.all()

    async def get_by_pk(
        self, session: AsyncSession, Model: Type[SQLModel], item_id: Any, rls_cond: Any
    ) -> Optional[Any]:
        pk = self._pk_name(Model)
        stmt = select(Model).where(Model.__table__.c[pk] == item_id)
        if rls_cond is not None:
            stmt = stmt.where(rls_cond)
        res = await session.exec(stmt)
        return res.first()

    async def create(self, session: AsyncSession, Model: Type[SQLModel], data: Dict[str, Any]) -> Any:
        obj = Model(**data)  # type: ignore
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def patch(
        self, session: AsyncSession, Model: Type[SQLModel],
        item_id: Any, changes: Dict[str, Any], rls_cond: Any
    ) -> Optional[Any]:
        obj = await self.get_by_pk(session, Model, item_id, rls_cond)
        if not obj:
            return None
        for k, v in changes.items():
            setattr(obj, k, v)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def delete(self, session: AsyncSession, Model: Type[SQLModel], item_id: Any, rls_cond: Any) -> bool:
        obj = await self.get_by_pk(session, Model, item_id, rls_cond)
        if not obj:
            return False
        await session.delete(obj)
        await session.commit()
        return True
