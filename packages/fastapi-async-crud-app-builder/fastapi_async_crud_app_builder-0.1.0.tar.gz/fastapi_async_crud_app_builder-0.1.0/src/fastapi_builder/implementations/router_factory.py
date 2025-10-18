from typing import Optional, Dict, Type, Any

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from ..types import GetUserDep, GetSessionDep, UserIdExtractor, AppConfig

from .pluralizer import SimplePluralizer
from .rls import OwnerColumnRLS
from .schemas import DefaultSchemaFactory
from .backend import SqlModelAsyncBackend

from ..protocols import AsyncCrudBackend, RLSStrategy, SchemaFactory, Pluralizer

from fastapi import APIRouter, Depends, Query, HTTPException, Body

class AsyncCrudFactory:
    def __init__(
        self,
        models: Dict[str, Type[SQLModel]],
        app_config: AppConfig,
        get_session_dep: GetSessionDep,
        get_user_dep: GetUserDep,
        *,
        user_id_extractor: UserIdExtractor,
        backend: Optional[AsyncCrudBackend] = None,
        rls_strategy: Optional[RLSStrategy] = None,
        schema_factory: Optional[SchemaFactory] = None,
        pluralizer: Optional[Pluralizer] = None,
        tag_prefix: Optional[str] = None,
        max_limit: int = 500,
    ) -> None:
        self.models = {k.lower(): v for k, v in models.items()}
        self.app = app_config
        self.get_session_dep = get_session_dep
        self.get_user_dep = get_user_dep

        self.backend = backend or SqlModelAsyncBackend()
        self.rls = rls_strategy or OwnerColumnRLS(user_id_extractor, app_config.rls_column_name)
        self.schemas = schema_factory or DefaultSchemaFactory()
        self.pluralizer = pluralizer or SimplePluralizer()
        self.tag_prefix = tag_prefix or app_config.slug
        self.max_limit = max_limit

    def build_router(self) -> APIRouter:
        top = APIRouter(prefix=f"/api/{self.app.slug}")
        for name, Model in self.models.items():
            sub = self._build_model_router(name, Model)  # <- Model bound here
            top.include_router(sub)
        return top
    
    def _build_model_router(self, name: str, Model: type[SQLModel]) -> APIRouter:
        plural = self.pluralizer.pluralize(name)
        tag = f"{self.tag_prefix}:{name}"
        sub = APIRouter(prefix=f"/{plural}", tags=[tag])

        QueryModel  = self.schemas.make_query(Model)
        UpdateModel = self.schemas.make_update(Model)
        CreateModel = self.schemas.make_create(Model, self._rls_col(Model))

        @sub.get("", name=f"list_{name}")
        async def list_items(
            session: AsyncSession = Depends(self.get_session_dep),
            user: Any = Depends(self.get_user_dep),
            limit: int = Query(50, ge=1, le=self.max_limit),
            offset: int = Query(0, ge=0),
            params: QueryModel = Depends(),  # type: ignore
        ):
            rls_cond = self.rls.condition(Model, user)
            filters = params.model_dump(exclude_unset=True)
            return await self.backend.list(session, Model, filters, limit, offset, rls_cond)

        @sub.get("/{item_id}", name=f"get_{name}")
        async def get_item(
            item_id: Any,
            session: AsyncSession = Depends(self.get_session_dep),
            user: Any = Depends(self.get_user_dep),
        ):
            rls_cond = self.rls.condition(Model, user)
            obj = await self.backend.get_by_pk(session, Model, item_id, rls_cond)
            if not obj:
                raise HTTPException(404, "Not found")
            return obj

        @sub.post("", name=f"create_{name}")
        async def create_item(
            payload: CreateModel = Body(...),  # type: ignore
            session: AsyncSession = Depends(self.get_session_dep),
            user: Any = Depends(self.get_user_dep),
        ):
            data = payload.model_dump(exclude_unset=True)
            self.rls.inject_on_create(Model, data, user)
            return await self.backend.create(session, Model, data)

        @sub.patch("/{item_id}", name=f"update_{name}")
        async def update_item(
            item_id: Any,
            payload: UpdateModel = Body(...),  # type: ignore
            session: AsyncSession = Depends(self.get_session_dep),
            user: Any = Depends(self.get_user_dep),
        ):
            rls_cond = self.rls.condition(Model, user)
            current = await self.backend.get_by_pk(session, Model, item_id, rls_cond)
            if not current:
                raise HTTPException(404, "Not found")
            changes = payload.model_dump(exclude_unset=True)
            self.rls.guard_update(Model, current, changes, user)
            obj = await self.backend.patch(session, Model, item_id, changes, rls_cond)
            if not obj:
                raise HTTPException(404, "Not found")
            return obj

        @sub.delete("/{item_id}", name=f"delete_{name}")
        async def delete_item(
            item_id: Any,
            session: AsyncSession = Depends(self.get_session_dep),
            user: Any = Depends(self.get_user_dep),
        ):
            rls_cond = self.rls.condition(Model, user)
            ok = await self.backend.delete(session, Model, item_id, rls_cond)
            if not ok:
                raise HTTPException(404, "Not found")
            return {"status": "deleted", "id": item_id}

        return sub


    def _rls_col(self, Model: Type[SQLModel]) -> Optional[str]:
        col = self.app.rls_column_name
        return col if col and col in Model.__table__.c else None
