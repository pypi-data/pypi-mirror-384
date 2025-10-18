from typing import Callable, Dict, Type, Any, Optional, List

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .router_factory import AsyncCrudFactory

from .auth_builder import AsyncAuthBuilder, JWTConfig

from ..protocols import AsyncCrudBackend, Pluralizer, SchemaFactory, RLSStrategy
from ..types import AppConfig

class DynamicCrudAppBuilder:
    def __init__(
        self,
        *,
        # Core
        models: Dict[str, Type[SQLModel]],
        app_config: AppConfig,
        user_id_extractor: Callable[[Any], Any],
        get_user_dep: Callable[..., Any] = None,

        # DB wiring: pass engine OR database_url; you can also pass a session_maker directly
        engine: Optional[AsyncEngine] = None,
        database_url: Optional[str] = None,
        session_maker: Optional[async_sessionmaker[AsyncSession]] = None,

        # Injection points (can be None → defaults used by AsyncCrudFactory)
        backend: Optional[AsyncCrudBackend] = None,
        rls_strategy: Optional[RLSStrategy] = None,
        schema_factory: Optional[SchemaFactory] = None,
        pluralizer: Optional[Pluralizer] = None,

        # App settings
        title: str = "Dynamic CRUD",
        openapi_url: str = "/openapi.json",
        docs_url: str = "/docs",
        redoc_url: Optional[str] = "/redoc",
        enable_cors: bool = True,
        cors_origins: Optional[List[str]] = None,
        echo_sql: bool = False,
        create_all_on_startup: bool = True,
        tag_prefix: Optional[str] = None,
        max_limit: int = 500,

        auth_user_model: Optional[Type[SQLModel]] = None,
        auth_identification_attr: str = "email",
        auth_password_attr: str = "password",
        auth_is_active_attr: Optional[str] = "is_active",
        auth_jwt_config: Optional[JWTConfig] = None,
        auth_token_url: str = "/auth/login",
        mount_auth_router: bool = True,
    ) -> None:
        self._models: Dict[str, Type[SQLModel]] = {k.lower(): v for k, v in models.items()}
        self._app_cfg = app_config
        self._get_user_dep = get_user_dep
        self._user_id_extractor = user_id_extractor

        self._engine = engine
        self._database_url = database_url
        self._session_maker = session_maker

        self._backend = backend
        self._rls_strategy = rls_strategy
        self._schema_factory = schema_factory
        self._pluralizer = pluralizer

        self._title = title
        self._openapi_url = openapi_url
        self._docs_url = docs_url
        self._redoc_url = redoc_url
        self._enable_cors = enable_cors
        self._cors_origins = cors_origins or ["*"]
        self._echo_sql = echo_sql
        self._create_all_on_startup = create_all_on_startup
        self._tag_prefix = tag_prefix or app_config.slug
        self._max_limit = max_limit

        self._auth_user_model = auth_user_model
        self._auth_ident_attr = auth_identification_attr
        self._auth_pass_attr = auth_password_attr
        self._auth_is_active_attr = auth_is_active_attr
        self._auth_jwt_cfg = auth_jwt_config
        self._auth_token_url = auth_token_url
        self._mount_auth_router = mount_auth_router

        self._created_engine_here = False
        self._fastapi: Optional[FastAPI] = None

    # ---------------- public API ----------------
    def add_model(self, name: str, model: Type[SQLModel]) -> "DynamicCrudAppBuilder":
        self._models[name.lower()] = model
        return self

    def add_models(self, models: Dict[str, Type[SQLModel]]) -> "DynamicCrudAppBuilder":
        for k, v in models.items():
            self.add_model(k, v)
        return self

    def set_backend(self, backend: AsyncCrudBackend) -> "DynamicCrudAppBuilder":
        self._backend = backend
        return self

    def set_rls_strategy(self, rls: RLSStrategy) -> "DynamicCrudAppBuilder":
        self._rls_strategy = rls
        return self

    def set_schema_factory(self, factory: SchemaFactory) -> "DynamicCrudAppBuilder":
        self._schema_factory = factory
        return self

    def set_pluralizer(self, pluralizer: Pluralizer) -> "DynamicCrudAppBuilder":
        self._pluralizer = pluralizer
        return self

    def build(self) -> FastAPI:
        """
        Create and wire the FastAPI app:
          - DB engine/session deps
          - Async CRUD router for all models
          - CORS + OpenAPI routes
          - Optional table creation on startup
        """
        self._ensure_db()
        get_session_dep = self._make_session_dependency()

        auth_router = None
        if self._auth_user_model and self._auth_jwt_cfg:
            # Create auth module and mount its router
            auth_builder = AsyncAuthBuilder(
                user_model=self._auth_user_model,
                identification_attr=self._auth_ident_attr,
                password_attr=self._auth_pass_attr,
                is_active_attr=self._auth_is_active_attr,
                get_session=get_session_dep,
                jwt_config=self._auth_jwt_cfg,
                token_url=self._auth_token_url,
            )
            auth_router, get_current_user = auth_builder.build()

            # If caller didn't provide a custom dependency, use the auth one
            if self._get_user_dep is None:
                self._get_user_dep = get_current_user

        # If RLS is enabled (rls_column_name set) but we still have no auth dependency → error
        if (self._app_cfg.rls_column_name and self._get_user_dep is None):
            raise HTTPException(
                status_code=500,
                detail=(
                    "RLS is enabled but no auth dependency is configured. "
                    "Provide either: get_user_dep=... OR auth_* params (user model + jwt config)."
                ),
            )

        # Build the CRUD router via injected factory
        router_factory = AsyncCrudFactory(
            models=self._models,
            app_config=self._app_cfg,
            get_session_dep=get_session_dep,
            get_user_dep=self._get_user_dep,
            user_id_extractor=self._user_id_extractor,
            backend=self._backend,
            rls_strategy=self._rls_strategy,
            schema_factory=self._schema_factory,
            pluralizer=self._pluralizer,
            tag_prefix=self._tag_prefix,
            max_limit=self._max_limit,
        )
        router = router_factory.build_router()

        # Create FastAPI app
        app = FastAPI(
            title=self._title,
            openapi_url=self._openapi_url,
            docs_url=self._docs_url,
            redoc_url=self._redoc_url,
        )

        if self._enable_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self._cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        if auth_router and self._mount_auth_router:
            app.include_router(auth_router)

        app.include_router(router)

        if self._engine is not None and self._create_all_on_startup:
            @app.on_event("startup")
            async def _startup_create_tables() -> None:
                async with self._engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)

        self._fastapi = app
        return app

    # ---------------- internals ----------------
    def _ensure_db(self) -> None:
        if self._engine is None and self._database_url:
            self._engine = create_async_engine(self._database_url, echo=self._echo_sql, future=True)
            self._created_engine_here = True

        if self._session_maker is None and self._engine is not None:
            self._session_maker = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    def _make_session_dependency(self) -> Callable[..., AsyncSession]:
        async def _dep():
            if self._session_maker is None:
                raise RuntimeError(
                    "Session maker not configured. Provide engine/database_url, "
                    "or pass your own session_maker when constructing the builder."
                )
            async with self._session_maker() as session:
                yield session
        return _dep
