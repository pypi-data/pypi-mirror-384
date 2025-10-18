#from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple, Type

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, create_model, Field as PydField
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from passlib.context import CryptContext


class JWTConfig(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expires_minutes: int = 60
    issuer: Optional[str] = None
    audience: Optional[str] = None
    subject_claim: str = "sub"  # will store the user's PRIMARY KEY value


class AsyncAuthBuilder:
    def __init__(
        self,
        *,
        user_model: Type[SQLModel],
        identification_attr: str,
        password_attr: str,
        get_session: Callable[..., AsyncSession] | Callable[..., Any],
        jwt_config: JWTConfig,
        is_active_attr: Optional[str] = "is_active",
        token_url: str = "/auth/login",
        pwd_context: Optional[CryptContext] = None,
    ) -> None:
        self.User = user_model
        self.ident_attr = identification_attr
        self.pass_attr = password_attr
        self.is_active_attr = is_active_attr
        self.get_session = get_session
        self.jwt = jwt_config
        self.token_url = token_url
        self.pwd = pwd_context or CryptContext(schemes=["bcrypt"], deprecated="auto")

        self._oauth2 = HTTPBearer()

        # dynamic DTOs
        self.CreateUserDTO, self.LoginDTO, self.UserReadDTO = self._make_dtos()

        for _m in (self.CreateUserDTO, self.LoginDTO, self.UserReadDTO):
            try:
                _m.model_rebuild()  # pydantic v2 requirement for dynamic models
            except Exception:
                pass

    # ---------- public API ----------
    def build(self) -> Tuple[APIRouter, Callable[..., Any]]:
        """
        Returns (router, get_current_user dependency)
        """
        router = APIRouter(prefix="/auth", tags=["Auth"])

        CreateUserDTO = self.CreateUserDTO
        UserReadDTO   = self.UserReadDTO
        TokenDTO      = self._TokenDTO()

        for _m in (CreateUserDTO, UserReadDTO, TokenDTO):
            try:
                TokenDTO.model_rebuild()
            except Exception:
                pass

        User          = self.User
        ident_attr    = self.ident_attr
        pass_attr     = self.pass_attr
        is_active_attr = self.is_active_attr

        security        = self._oauth2
        get_session   = self.get_session
        jwt_cfg       = self.jwt

        _hash         = self._hash
        _verify       = self._verify
        _pk_name      = self._pk_name()
        _user_pk      = lambda u: getattr(u, _pk_name)

        async def get_current_user(
            token: HTTPAuthorizationCredentials = Depends(security),
            session: AsyncSession = Depends(get_session),
        ):
            print(token)
            claims = self._decode_token(token.credentials)
            sub = claims.get(jwt_cfg.subject_claim)
            if sub is None:
                raise HTTPException(401, "Invalid token", headers={"WWW-Authenticate": "Bearer"})
            pk_col = getattr(User, _pk_name)
            res = await session.exec(select(User).where(pk_col == sub))
            user = res.first()
            if not user:
                raise HTTPException(401, "User not found", headers={"WWW-Authenticate": "Bearer"})
            if is_active_attr and not getattr(user, is_active_attr, True):
                raise HTTPException(403, "Inactive user")
            return user

        @router.post("/register", response_model=self.UserReadDTO)  # type: ignore[arg-type]
        async def register(payload: User = Body(...),  # type: ignore[name-defined]
                           session: AsyncSession = Depends(self.get_session)):
            data = payload.model_dump(exclude_unset=True)
            ident_val = data.get(self.ident_attr)
            raw_pw = data.get(self.pass_attr)

            if not ident_val or not raw_pw:
                raise HTTPException(400, f"Both '{self.ident_attr}' and '{self.pass_attr}' are required.")

            # uniqueness check
            ident_col = getattr(self.User, self.ident_attr, None)
            if ident_col is None:
                raise HTTPException(500, f"Bad configuration: {self.User.__name__}.{self.ident_attr} missing")
            exists_q = select(self.User).where(ident_col == ident_val)
            if (await session.exec(exists_q)).first():
                raise HTTPException(409, "User already exists")

            # hash password + create user
            data[self.pass_attr] = self._hash(raw_pw)
            user = self.User(**data)  # type: ignore
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return self._sanitize_user(user)

        @router.post("/login", response_model=self._TokenDTO())
        async def login(form: OAuth2PasswordRequestForm = Depends(),
                        session: AsyncSession = Depends(self.get_session)):
            # OAuth2PasswordRequestForm fields: username, password
            ident_val = form.username
            raw_pw = form.password

            user = await self._find_by_ident(session, ident_val)
            if not user or not self._verify(raw_pw, getattr(user, self.pass_attr, "")):
                raise HTTPException(status_code=401, detail="Invalid credentials",
                                    headers={"WWW-Authenticate": "Bearer"})
            if self.is_active_attr and not getattr(user, self.is_active_attr, True):
                raise HTTPException(status_code=403, detail="Inactive user")

            subject = self._user_pk_value(user)
            access_token = self._create_access_token(subject)
            return {"access_token": access_token, "token_type": "bearer"}

        @router.get("/me", response_model=self.UserReadDTO)  # type: ignore[arg-type]
        async def me(user=Depends(get_current_user)):
            return self._sanitize_user(user)

        return router, get_current_user

    # ---------- dependency ----------
    async def get_current_user(self,
                               token: str = Depends(lambda: None),
                               session: AsyncSession = Depends(lambda: None)):
        """
        This is replaced below with a closure binding OAuth2 & session dep.
        (FastAPI needs a concrete dependency; we'll wrap properly in __post_init__)
        """
        raise RuntimeError("Call build() and use the returned dependency")

    def __post_init_dependency(self):
        oauth2 = self._oauth2
        get_session = self.get_session
        jwt_cfg = self.jwt
        User = self.User
        pk_name = self._pk_name()

        async def _dep(token: str = Depends(oauth2),
                       session: AsyncSession = Depends(get_session)):
            claims = self._decode_token(token)
            sub = claims.get(jwt_cfg.subject_claim)
            if sub is None:
                raise HTTPException(401, "Invalid token", headers={"WWW-Authenticate": "Bearer"})

            pk_col = getattr(User, pk_name)
            res = await session.exec(select(User).where(pk_col == sub))
            user = res.first()
            if not user:
                raise HTTPException(401, "User not found", headers={"WWW-Authenticate": "Bearer"})
            if self.is_active_attr and not getattr(user, self.is_active_attr, True):
                raise HTTPException(403, "Inactive user")
            return user

        # monkey-patch the instance method to the bound closure
        object.__setattr__(self, "get_current_user", _dep)

    async def _find_by_ident(self, session: AsyncSession, ident_val: Any):
        """
        Fetch a user by the identification attribute (e.g., email/username).
        Returns the user instance or None.
        """
        ident_col = getattr(self.User, self.ident_attr, None)
        if ident_col is None:
            raise RuntimeError(
                f"Bad configuration: {self.User.__name__}.{self.ident_attr} doesn't exist"
            )
        result = await session.exec(select(self.User).where(ident_col == ident_val))
        return result.first()


    # ---------- internals ----------
    def _make_dtos(self) -> Tuple[Type[BaseModel], Type[BaseModel], Type[BaseModel]]:
        # CreateUserDTO
        fields: Dict[str, Tuple[type, Any]] = {}
        for c in self.User.__table__.columns:
            py = self._safe_py_type(c.type)
            if c.primary_key:
                continue
            # require identifier + password, else honor column nullability
            if c.name == self.ident_attr or c.name == self.pass_attr:
                fields[c.name] = (py, ...)  # required
            else:
                fields[c.name] = (Optional[py], None)
        CreateUserDTO = create_model(f"Create{self.User.__name__}", **fields)  # type: ignore

        LoginDTO = create_model(
            f"Login{self.User.__name__}",
            **{
                self.ident_attr: (str, ...),
                self.pass_attr: (str, ...),
            },
        )

        out_fields: Dict[str, Tuple[type, Any]] = {}
        for c in self.User.__table__.columns:
            if c.name == self.pass_attr:
                continue
            py = self._safe_py_type(c.type)
            out_fields[c.name] = (Optional[py], None if getattr(c, "nullable", True) else ...)
        UserReadDTO = create_model(f"{self.User.__name__}Read", **out_fields)  # type: ignore

        return CreateUserDTO, LoginDTO, UserReadDTO

    def _TokenDTO(self) -> Type[BaseModel]:
        return create_model("TokenDTO",
                            access_token=(str, ...),
                            token_type=(str, PydField(default="bearer")))  # type: ignore

    def _pk_name(self) -> str:
        for c in self.User.__table__.columns:
            if c.primary_key:
                return c.name
        raise RuntimeError(f"{self.User.__name__} has no primary key")

    def _user_pk_value(self, user: Any) -> Any:
        return getattr(user, self._pk_name())

    def _create_access_token(self, subject: Any) -> str:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=self.jwt.access_token_expires_minutes)
        payload: Dict[str, Any] = {
            self.jwt.subject_claim: str(subject),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        if self.jwt.issuer:
            payload["iss"] = self.jwt.issuer
        if self.jwt.audience:
            payload["aud"] = self.jwt.audience
        return jwt.encode(payload, self.jwt.secret_key, algorithm=self.jwt.algorithm)

    def _decode_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                jwt = token,
                key = self.jwt.secret_key,
                algorithms=[self.jwt.algorithm]
            )
        except jwt.PyJWTError as e:
            print(str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    def _sanitize_user(self, user):
        return user

    def _hash(self, password: str) -> str:
        return self.pwd.hash(password)

    def _verify(self, password: str, hashed: str) -> bool:
        try:
            return self.pwd.verify(password, hashed)
        except Exception:
            return False

    def _safe_py_type(self, satype: Any) -> type:
        try:
            if hasattr(satype, "python_type"):
                return satype.python_type  # may raise
        except Exception:
            pass
        from sqlalchemy import Integer, String, Boolean, Float, DateTime, Date, LargeBinary
        try:
            if isinstance(satype, Integer): return int
            if isinstance(satype, String): return str
            if isinstance(satype, Boolean): return bool
            if isinstance(satype, Float): return float
            if isinstance(satype, DateTime):
                from datetime import datetime as _dt; return _dt
            if isinstance(satype, Date):
                from datetime import date as _d; return _d
            if isinstance(satype, LargeBinary): return bytes
        except Exception:
            pass
        visit = getattr(satype, "__visit_name__", "").lower()
        if "json" in visit: return dict
        if "uuid" in visit: return str
        if "array" in visit: return list
        return Any

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "jwt":  # after jwt is set in __init__, bind dependency
            try:
                self.__post_init_dependency()
            except Exception:
                pass
