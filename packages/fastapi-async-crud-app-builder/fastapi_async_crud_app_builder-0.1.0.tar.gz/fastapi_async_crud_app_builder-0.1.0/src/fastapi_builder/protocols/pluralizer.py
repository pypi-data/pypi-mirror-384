from typing import Protocol

class Pluralizer(Protocol):
    def pluralize(self, name: str) -> str: ...