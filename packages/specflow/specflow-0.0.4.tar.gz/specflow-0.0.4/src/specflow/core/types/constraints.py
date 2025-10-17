from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from specflow.typing import Object

T = TypeVar("T", str, int, float, bool, None)


class ConstraintError(Exception): ...


class Constraint(ABC, Generic[T]):
    @property
    @abstractmethod
    def _name(self) -> str: ...

    @property
    @abstractmethod
    def _value(self) -> T | list[T]: ...

    @abstractmethod
    def __call__(self, to_validate: T) -> None: ...

    def to_dict(self) -> Object:
        return {self._name: self._value}  # type: ignore


class Const(Constraint[T], Generic[T]):
    def __init__(self, const: T) -> None:
        self._const: T = const

    @property
    def _name(self) -> str:
        return "const"

    @property
    def _value(self) -> T:
        return self._const

    def __call__(self, to_validate: T) -> None:
        if to_validate != self._const:
            raise ConstraintError(
                f"Must equal {self._const!r}, got {to_validate!r}",
            )


class Enum(Constraint[T], Generic[T]):
    def __init__(self, enum: list[T]) -> None:
        if not enum:
            raise ValueError("Enum can't be empty.'")

        self._enum: list[T] = enum

    @property
    def _name(self) -> str:
        return "enum"

    @property
    def _value(self) -> list[T]:
        return self._enum

    def __call__(self, to_validate: T) -> None:
        if to_validate not in self._enum:
            raise ConstraintError(
                f"Must be one of {self._enum}, got {to_validate!r}",
            )
