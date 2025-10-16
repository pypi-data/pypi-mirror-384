from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from typing_extensions import override

from ._typing import JSON, E, T

if TYPE_CHECKING:
    from collections.abc import Sequence


## Base
class ConstraintError(Exception): ...


class Constraint(ABC, Generic[T]):
    @property
    @abstractmethod
    def _name(self) -> str: ...

    @property
    @abstractmethod
    def _value(self) -> T: ...

    @abstractmethod
    def __call__(self, to_validate: T) -> None: ...

    def to_dict(self) -> JSON:
        return {self._name: self._value}


## General Constraints
class Const(Constraint, Generic[T]):
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


class Enum(Constraint, Generic[T]):
    def __init__(self, enum: Sequence[T]) -> None:
        if not enum:
            raise ValueError("Enum can't be empty.'")

        self._enum: Sequence[T] = enum

    @property
    def _name(self) -> str:
        return "enum"

    @property
    def _value(self) -> T:
        return self._enum

    def __call__(self, to_validate: T) -> None:
        if to_validate not in self._enum:
            raise ConstraintError(
                f"Must be one of {self._enum}, got {to_validate!r}",
            )


## String Constraints
class MinLength(Constraint[str]):
    def __init__(self, min_: int) -> None:
        self._min: int = min_

    @property
    def _name(self) -> str:
        return "minLength"

    @property
    @override
    def _value(self) -> int:
        return self._min

    def __call__(self, to_validate: str) -> None:
        if (n := len(to_validate)) < self._min:
            raise ConstraintError(
                f"Length must be at least {self._min}, got {n}",
            )


class MaxLength(Constraint[str]):
    def __init__(self, max_: int) -> None:
        self._max: int = max_

    @property
    def _name(self) -> str:
        return "maxLength"

    @property
    def _value(self) -> int:
        return self._max

    def __call__(self, to_validate: str) -> None:
        if (n := len(to_validate)) > self._max:
            raise ConstraintError(
                f"Length must be at most {self._max}, got {n}",
            )


class Pattern(Constraint[str]):
    def __init__(self, pattern: str) -> None:
        self._pattern = re.compile(pattern)

    @property
    def _name(self) -> str:
        return "pattern"

    @property
    @override
    def _value(self) -> str:
        return self._pattern.pattern

    def __call__(self, to_validate: str) -> None:
        if self._pattern.search(to_validate) is None:
            raise ConstraintError(
                f"Must match pattern: {self._pattern.pattern}, got {to_validate}",
            )


## Integer Constraints
class Minimum(Constraint[int]):
    def __init__(self, min_: float) -> None:
        self._min: int | float = min_

    @property
    def _name(self) -> str:
        return "minimum"

    @property
    def _value(self) -> int | float:
        return self._min

    def __call__(self, to_validate: int) -> None:
        if to_validate < self._min:
            raise ConstraintError(
                f"Must be at least {self._min}, got {to_validate}",
            )


class Maximum(Constraint[int]):
    def __init__(self, max_: float) -> None:
        self._max: int | float = max_

    @property
    def _name(self) -> str:
        return "maximum"

    @property
    def _value(self) -> int | float:
        return self._max

    def __call__(self, to_validate: int) -> None:
        if to_validate > self._max:
            raise ConstraintError(
                f"Must be at most {self._max}, got {to_validate}",
            )


class ExclusiveMinimum(Constraint[int]):
    def __init__(self, min_: float) -> None:
        self._min: int | float = min_

    @property
    def _name(self) -> str:
        return "exclusiveMinimum"

    @property
    def _value(self) -> int | float:
        return self._min

    def __call__(self, to_validate: int) -> None:
        if to_validate <= self._min:
            raise ConstraintError(
                f"Must be greater than {self._min}, got {to_validate}",
            )


class ExclusiveMaximum(Constraint[int]):
    def __init__(self, max_: float) -> None:
        self._max: int | float = max_

    @property
    def _name(self) -> str:
        return "exclusiveMaximum"

    @property
    def _value(self) -> int | float:
        return self._max

    def __call__(self, to_validate: int) -> None:
        if to_validate >= self._max:
            raise ConstraintError(
                f"Must be less than {self._max}, got {to_validate}",
            )


class MultipleOf(Constraint[int]):
    def __init__(self, multiple: int) -> None:
        if multiple <= 0:
            raise ValueError("'multiple' must be greater than 0")

        self._multiple: int = multiple

    @property
    def _name(self) -> str:
        return "multipleOf"

    @property
    def _value(self) -> int:
        return self._multiple

    def __call__(self, to_validate: int) -> None:
        if to_validate % self._multiple != 0:
            raise ConstraintError(
                f"Must be a multiple of {self._multiple}, got {to_validate}",
            )


## Number Constraint
class Minimum(Constraint[float]):
    def __init__(self, min_: float) -> None:
        self._min: int | float = min_

    @property
    def _name(self) -> str:
        return "minimum"

    @property
    def _value(self) -> float:
        return self._min

    def __call__(self, to_validate: float) -> None:
        if to_validate < self._min:
            raise ConstraintError(
                f"Must be at least {self._min}, got {to_validate}",
            )


class Maximum(Constraint[float]):
    def __init__(self, max_: float) -> None:
        self._max: float = max_

    @property
    def _name(self) -> str:
        return "maximum"

    @property
    def _value(self) -> int | float:
        return self._max

    def __call__(self, to_validate: float) -> None:
        if to_validate > self._max:
            raise ConstraintError(
                f"Must be at most {self._max}, got {to_validate}",
            )


class ExclusiveMinimum(Constraint[float]):
    def __init__(self, min_: float) -> None:
        self._min: int | float = min_

    @property
    def _name(self) -> str:
        return "exclusiveMinimum"

    @property
    def _value(self) -> int | float:
        return self._min

    def __call__(self, to_validate: float) -> None:
        if to_validate <= self._min:
            raise ConstraintError(
                f"Must be greater than {self._min}, got {to_validate}",
            )


class ExclusiveMaximum(Constraint[float]):
    def __init__(self, max_: float) -> None:
        self._max: int | float = max_

    @property
    def _name(self) -> str:
        return "exclusiveMaximum"

    @property
    def _value(self) -> int | float:
        return self._max

    def __call__(self, to_validate: float) -> None:
        if to_validate >= self._max:
            raise ConstraintError(
                f"Must be less than {self._max}, got {to_validate}",
            )


class MultipleOf(Constraint[float]):
    def __init__(self, multiple: float) -> None:
        if multiple <= 0:
            raise ValueError("'multiple' must be greater than 0")

        self._multiple: float = multiple

    @property
    def _name(self) -> str:
        return "multipleOf"

    @property
    def _value(self) -> int | float:
        return self._multiple

    def __call__(self, to_validate: float) -> None:
        quotient = to_validate / self._multiple
        if abs(quotient - round(quotient)) > 1e-10:
            raise ConstraintError(
                f"Must be a multiple of {self._multiple}, got {to_validate}",
            )


## Array Constraints
class MinItems(Constraint[list[int]]):
    def __init__(self, min_: int) -> None:
        if min_ < 0:
            raise ValueError("'min' must be greater than or equal to 0.")

        self._min: int = min_

    @property
    def _name(self) -> str:
        return "minItems"

    @property
    def _value(self) -> int:
        return self._min

    def __call__(self, to_validate: list[E]) -> None:
        if (n := len(to_validate)) < self._min:
            raise ConstraintError(
                f"Must have at least {self._min} items, got {n}",
            )


class MaxItems(Constraint[list[int]]):
    def __init__(self, max_: int) -> None:
        if max_ < 0:
            raise ValueError(
                "'max' must be greater than or equal to 0.",
            )

        self._max: int = max_

    @property
    def _name(self) -> str:
        return "maxItems"

    @property
    def _value(self) -> int:
        return self._max

    def __call__(self, to_validate: list[int]) -> None:
        if (n := len(to_validate)) > self._max:
            raise ConstraintError(
                f"Must have at least {self._max} items, got {n}",
            )


class MinContains(Constraint[list[int]]):
    def __init__(self, min_: int) -> None:
        if min_ < 0:
            raise ValueError("'min' must be greater than or equal to 0.")

        self._min: int = min_

    @property
    def _name(self) -> str:
        return "minContains"

    @property
    def _value(self) -> int:
        return self._min

    def __call__(self, to_validate: list[int]) -> None:
        if (n := len(to_validate)) < self._min:
            raise ConstraintError(
                f"Must contain at least {self._min} matching items, got {n}",
            )


class MaxContains(Constraint[list[int]]):
    def __init__(self, max_: int) -> None:
        if max_ < 0:
            raise ValueError(
                "'max' must be greater than or equal to 0.",
            )

        self._max: int = max_

    @property
    def _name(self) -> str:
        return "maxContains"

    @property
    def _value(self) -> int:
        return self._max

    def __call__(self, to_validate: list[int]) -> None:
        if (n := len(to_validate)) > self._max:
            raise ConstraintError(
                f"Must contain at most {self._max} matching items, got {n}",
            )
