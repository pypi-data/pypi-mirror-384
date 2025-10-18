from typing import Callable, Any, Optional
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

GetSessionDep = Callable[..., AsyncSession]
GetUserDep = Callable[..., Any]
UserIdExtractor = Callable[[Any], Any]

class AppConfig(BaseModel):
    slug: str                                  # e.g. "library"
    rls_column_name: Optional[str] = "owner_id" # if present & in model -> enforced
