from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

B = TypeVar("B", bound=Enum)

@dataclass(frozen=True)
class ModelID(Generic[B]):
    brand: B
    model: str

    def key(self) -> str:
        return f"{self.brand.value}/{self.model}"

    def __str__(self) -> str:
        return f"{self.brand.value} {self.model}"

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return f"{cls}(brand={self.brand.name}, model={self.model!r})"
