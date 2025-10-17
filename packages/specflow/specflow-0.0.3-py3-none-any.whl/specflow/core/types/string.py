from __future__ import annotations

import re

from .constraints import Const, Constraint, ConstraintError, Enum
from .type import Type


class String(Type[str]):
    def __init__(
        self,
        title: str,
        description: str | None = None,
        default: str | None = None,
        const: str | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        enum: list[str] | None = None,
        constraints: list[Constraint[str]] | None = None,
        *,
        nullable: bool = False,
    ) -> None:
        constraints = constraints if constraints else []
        if const is not None:
            constraints.append(Const[str](const))
        if enum is not None:
            constraints.append(Enum(enum))
        if min_length is not None:
            constraints.append(MinLength(min_length))
        if max_length is not None:
            constraints.append(MaxLength(max_length))
        if pattern is not None:
            constraints.append(Pattern(pattern))

        super().__init__(title, description, default, constraints, nullable=nullable)

    @property
    def _type(self) -> str:
        return "string"


class MinLength(Constraint[str]):
    def __init__(self, min_: int) -> None:
        self._minimum: int = min_

    @property
    def _name(self) -> str:
        return "minLength"

    @property
    def _value(self) -> int:  # type: ignore
        return self._minimum

    def __call__(self, to_validate: str) -> None:
        if (n := len(to_validate)) < self._minimum:
            raise ConstraintError(
                f"Length must be at least {self._minimum}, got {n}",
            )


class MaxLength(Constraint[str]):
    def __init__(self, maximum: int) -> None:
        self._maximum: int = maximum

    @property
    def _name(self) -> str:
        return "maxLength"

    @property
    def _value(self) -> int:  # type: ignore
        return self._maximum

    def __call__(self, to_validate: str | None) -> None:
        if to_validate is None:
            return

        if (n := len(to_validate)) > self._maximum:
            raise ConstraintError(
                f"Length must be at most {self._maximum}, got {n}",
            )


class Pattern(Constraint[str]):
    def __init__(self, pattern: str) -> None:
        self._pattern = re.compile(pattern)

    @property
    def _name(self) -> str:
        return "pattern"

    @property
    def _value(self) -> str:
        return self._pattern.pattern

    def __call__(self, to_validate: str) -> None:
        if self._pattern.search(to_validate) is None:
            raise ConstraintError(
                f"Must match pattern: {self._pattern.pattern}, got {to_validate}",
            )
