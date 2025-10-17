from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from specflow.typing import Object

    from .constraints import Constraint

T = TypeVar("T", str, int, float, bool)


class Type(ABC, Generic[T]):
    def __init__(
        self,
        title: str,
        description: str | None = None,
        default: T | None = None,
        constraints: list[Constraint[T]] | None = None,
        *,
        nullable: bool = False,
    ) -> None:
        self._title: str = title
        self._description: str | None = description
        self._default: T | None = default
        self._constraints: list[Constraint[T]] | None = constraints
        self._nullable: bool = nullable

    @property
    @abstractmethod
    def _type(self) -> str: ...

    @property
    def title(self) -> str:
        return self._title

    def _validate(self, to_validate: T | None) -> None:
        if to_validate is None:
            return

        if self._constraints:
            for constraint in self._constraints:
                constraint(to_validate)

    def __call__(self, to_validate: T | None) -> None:
        self._validate(to_validate)

    def to_dict(self) -> Object:
        data: Object = {"type": self._type, "nullable": self._nullable}

        if self._description is not None:
            data["description"] = self._description
        if self._default is not None:
            data["default"] = self._default
        if self._constraints:
            for constraint in self._constraints:
                data.update(constraint.to_dict())

        return {self._title: data}
