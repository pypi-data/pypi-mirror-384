from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from ._typing import JSON, T

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .constraints import Constraint


## Base Type
class Type(ABC, Generic[T]):
    def __init__(
        self,
        title: str,
        description: str | None = None,
        constraints: Sequence[Constraint[T]] | None = None,
    ) -> None:
        self._title: str = title
        self._description: str | None = description
        self._constraints: Sequence[Constraint[T]] | None = constraints

    @property
    @abstractmethod
    def _type(self) -> str: ...

    @property
    def title(self) -> str:
        return self._title

    def _validate(self, to_validate: T) -> None:
        if self._constraints:
            for constraint in self._constraints:
                constraint(to_validate)

    def __call__(self, to_validate: T) -> None:
        self._validate(to_validate)

    def to_dict(self) -> JSON:
        data: JSON = {"type": self._type}

        if self._description is not None:
            data["description"] = self._description
        if self._constraints:
            for constraint in self._constraints:
                data.update(constraint.to_dict())

        return {self._title: data}


## String Type
class String(Type[str]):
    @property
    def _type(self) -> str:
        return "string"


## Integer Type
class Integer(Type[int]):
    @property
    def _type(self) -> str:
        return "integer"


## Number Type
class Number(Type[float]):
    @property
    def _type(self) -> str:
        return "number"


## Boolean Type
class Boolean(Type[bool]):
    @property
    def _type(self) -> str:
        return "boolean"


## Null Type
class Null(Type[None]):
    @property
    def _type(self) -> str:
        return "null"
