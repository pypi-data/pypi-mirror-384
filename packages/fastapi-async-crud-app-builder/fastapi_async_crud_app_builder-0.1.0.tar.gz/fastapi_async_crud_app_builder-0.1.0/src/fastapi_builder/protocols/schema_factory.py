from typing import Protocol, Type, Optional
from pydantic import BaseModel
from sqlmodel import SQLModel

class SchemaFactory(Protocol):
    """Produces Pydantic DTOs for query/create/update."""
    def make_query(self, Model: Type[SQLModel]) -> Type[BaseModel]: ...
    def make_create(self, Model: Type[SQLModel], rls_col: Optional[str]) -> Type[BaseModel]: ...
    def make_update(self, Model: Type[SQLModel]) -> Type[BaseModel]: ...


