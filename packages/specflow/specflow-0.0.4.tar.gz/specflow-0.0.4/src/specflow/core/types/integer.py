from __future__ import annotations

from .constraints import Constraint, ConstraintError
from .type import Type


class Integer(Type[int]):
    def __init__(
        self,
        title: str,
        description: str | None = None,
        default: int | None = None,
        minimum: int | None = None,
        maximum: int | None = None,
        exclusive_minimum: int | None = None,
        exclusive_maximum: int | None = None,
        mult: int | None = None,
        constraints: list[Constraint[int]] | None = None,
        *,
        nullable: bool = False,
    ) -> None:
        constraints = constraints if constraints else []
        if minimum is not None:
            constraints.append(Minimum(minimum))
        if maximum is not None:
            constraints.append(Maximum(maximum))
        if exclusive_minimum is not None:
            constraints.append(ExclusiveMinimum(exclusive_minimum))
        if exclusive_maximum is not None:
            constraints.append(ExclusiveMaximum(exclusive_maximum))
        if mult is not None:
            constraints.append(MultipleOf(mult))

        super().__init__(title, description, default, constraints, nullable=nullable)

    @property
    def _type(self) -> str:
        return "integer"


class Minimum(Constraint[int]):
    def __init__(self, minimum: int) -> None:
        self._minimum: int = minimum

    @property
    def _name(self) -> str:
        return "minimum"

    @property
    def _value(self) -> int:
        return self._minimum

    def __call__(self, to_validate: int | None) -> None:
        if to_validate is None:
            return

        if to_validate < self._minimum:
            raise ConstraintError(
                f"Must be at least {self._minimum}, got {to_validate}",
            )


class Maximum(Constraint[int]):
    def __init__(self, maximum: int) -> None:
        self._maximum: int = maximum

    @property
    def _name(self) -> str:
        return "maximum"

    @property
    def _value(self) -> int:
        return self._maximum

    def __call__(self, to_validate: int | None) -> None:
        if to_validate is None:
            return

        if to_validate > self._maximum:
            raise ConstraintError(
                f"Must be at most {self._maximum}, got {to_validate}",
            )


class ExclusiveMinimum(Constraint[int]):
    def __init__(self, minimum: int) -> None:
        self._minimum: int = minimum

    @property
    def _name(self) -> str:
        return "exclusiveMinimum"

    @property
    def _value(self) -> int:
        return self._minimum

    def __call__(self, to_validate: int | None) -> None:
        if to_validate is None:
            return

        if to_validate <= self._minimum:
            raise ConstraintError(
                f"Must be greater than {self._minimum}, got {to_validate}",
            )


class ExclusiveMaximum(Constraint[int]):
    def __init__(self, maximum: int) -> None:
        self._maximum: int = maximum

    @property
    def _name(self) -> str:
        return "exclusiveMaximum"

    @property
    def _value(self) -> int:
        return self._maximum

    def __call__(self, to_validate: int | None) -> None:
        if to_validate is None:
            return

        if to_validate >= self._maximum:
            raise ConstraintError(
                f"Must be less than {self._maximum}, got {to_validate}",
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

    def __call__(self, to_validate: int | None) -> None:
        if to_validate is None:
            return

        if to_validate % self._multiple != 0:
            raise ConstraintError(
                f"Must be a multiple of {self._multiple}, got {to_validate}",
            )
