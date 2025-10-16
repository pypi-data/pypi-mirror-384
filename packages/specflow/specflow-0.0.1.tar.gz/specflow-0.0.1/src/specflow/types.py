from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from ._typing import JSON, E, T

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


class ArrayType(Type[list[E]], Generic[E]):
    def __init__(
        self,
        title: str,
        description: str | None = None,
        item_constraints: Sequence[Constraint[list[E]]] | None = None,
        constraints: Sequence[Constraint[E]] | None = None,
    ) -> None:
        super().__init__(title=title, description=description, constraints=constraints)

        self._item_constraints: Sequence[Constraint[E]] = item_constraints

    def _validate_items(self, to_validate: list[E]) -> None:
        for item_constraint in self._item_constraints:
            item_constraint(to_validate)

    def __call__(self, to_validate: T) -> None:
        super().__call__(to_validate)
        self._validate_items(to_validate)

    def to_dict(self) -> JSON:
        data: JSON = super().to_dict()

        for constraint in self._item_constraints:
            data.update(constraint.to_dict())

        return data


## String Schemas
class String(Type[str]):
    @property
    def _type(self) -> str:
        return "string"


class StringArray(ArrayType[str]):
    @property
    def _type(self) -> str:
        return "stringArray"


## Integer Schemas
class Integer(Type[int]):
    @property
    def _type(self) -> str:
        return "integer"


class IntegerArray(ArrayType[int]):
    @property
    def _type(self) -> str:
        return "integerArray"


## Number Schemas
class Number(Type[float]):
    @property
    def _type(self) -> str:
        return "number"


class NumberArray(ArrayType[float]):
    @property
    def _type(self) -> str:
        return "numberArray"


## Boolean Schema
class Boolean(Type[bool]):
    @property
    def _type(self) -> str:
        return "boolean"


class BooleanArray(ArrayType[bool]):
    @property
    def _type(self) -> str:
        return "booleanArray"


## Null Schema
class Null(Type[None]):
    @property
    def _type(self) -> str:
        return "null"


class NullArray(ArrayType[None]):
    @property
    def _type(self) -> str:
        return "nullArray"
