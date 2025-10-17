from __future__ import annotations

from .constraints import Constraint, ConstraintError
from .type import Type


class Number(Type[float]):
    def __init__(
        self,
        title: str,
        description: str | None = None,
        default: float | None = None,
        minimum: float | None = None,
        maximum: float | None = None,
        exclusive_minimum: float | None = None,
        excluvie_maximum: float | None = None,
        mult: float | None = None,
        constraints: list[Constraint[float]] | None = None,
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
        if excluvie_maximum is not None:
            constraints.append(ExclusiveMaximum(excluvie_maximum))
        if mult is not None:
            constraints.append(MultipleOf(mult))

        super().__init__(title, description, default, constraints, nullable=nullable)

    @property
    def _type(self) -> str:
        return "number"


class Minimum(Constraint[float]):
    def __init__(self, min_: float) -> None:
        self._minimum: float = min_

    @property
    def _name(self) -> str:
        return "minimum"

    @property
    def _value(self) -> float:
        return self._minimum

    def __call__(self, to_validate: float | None) -> None:
        if to_validate is None:
            return

        if to_validate < self._minimum:
            raise ConstraintError(
                f"Must be at least {self._minimum}, got {to_validate}",
            )


class Maximum(Constraint[float]):
    def __init__(self, maximum: float) -> None:
        self._maximum: float = maximum

    @property
    def _name(self) -> str:
        return "maximum"

    @property
    def _value(self) -> float:
        return self._maximum

    def __call__(self, to_validate: float | None) -> None:
        if to_validate is None:
            return

        if to_validate > self._maximum:
            raise ConstraintError(
                f"Must be at most {self._maximum}, got {to_validate}",
            )


class ExclusiveMinimum(Constraint[float]):
    def __init__(self, minimum: float) -> None:
        self._minimum: float = minimum

    @property
    def _name(self) -> str:
        return "exclusiveMinimum"

    @property
    def _value(self) -> float:
        return self._minimum

    def __call__(self, to_validate: float | None) -> None:
        if to_validate is None:
            return

        if to_validate <= self._minimum:
            raise ConstraintError(
                f"Must be greater than {self._minimum}, got {to_validate}",
            )


class ExclusiveMaximum(Constraint[float]):
    def __init__(self, maximum: float) -> None:
        self._maximum: float = maximum

    @property
    def _name(self) -> str:
        return "exclusiveMaximum"

    @property
    def _value(self) -> float:
        return self._maximum

    def __call__(self, to_validate: float | None) -> None:
        if to_validate is None:
            return

        if to_validate >= self._maximum:
            raise ConstraintError(
                f"Must be less than {self._maximum}, got {to_validate}",
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
    def _value(self) -> float:
        return self._multiple

    def __call__(self, to_validate: float | None) -> None:
        if to_validate is None:
            return

        quotient = to_validate / self._multiple
        if abs(quotient - round(quotient)) > 1e-10:  # noqa: PLR2004
            raise ConstraintError(
                f"Must be a multiple of {self._multiple}, got {to_validate}",
            )
