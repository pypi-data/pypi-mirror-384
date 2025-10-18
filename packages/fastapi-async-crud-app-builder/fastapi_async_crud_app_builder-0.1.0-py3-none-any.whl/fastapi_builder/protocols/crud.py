from typing import Protocol, Type, Optional, Any, Dict

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel


class AsyncCrudBackend(Protocol):
    """Abstract data access. Replace with your own (e.g., calls to another service)."""
    async def list(
        self, session: AsyncSession, Model: Type[SQLModel],
        filters: Dict[str, Any], limit: int, offset: int, rls_cond: Any
    ) -> list[Any]: ...
    async def get_by_pk(
        self, session: AsyncSession, Model: Type[SQLModel], item_id: Any, rls_cond: Any
    ) -> Optional[Any]: ...
    async def create(
        self, session: AsyncSession, Model: Type[SQLModel], data: Dict[str, Any]
    ) -> Any: ...
    async def patch(
        self, session: AsyncSession, Model: Type[SQLModel], item_id: Any,
        changes: Dict[str, Any], rls_cond: Any
    ) -> Optional[Any]: ...
    async def delete(
        self, session: AsyncSession, Model: Type[SQLModel], item_id: Any, rls_cond: Any
    ) -> bool: ...
