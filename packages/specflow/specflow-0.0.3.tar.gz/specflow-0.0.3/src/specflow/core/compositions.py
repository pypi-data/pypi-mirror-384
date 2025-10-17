from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specflow.core.types import Boolean, Integer, Number, String
    from specflow.typing import Object

    from .schema import Schema


## Base
class CompositionError(Exception): ...


class Composition(ABC):
    def __init__(
        self,
        *items: Schema | String | Number | Integer | Boolean,
    ) -> None:
        if not items:
            raise ValueError("'items' cannot be empty.")

        self._items: dict[str, Schema | String | Number | Integer | Boolean] = {
            item.title: item for item in items
        }

        self._options: set[str] = set(self._items.keys())

    @property
    @abstractmethod
    def _name(self) -> str: ...

    @abstractmethod
    def __call__(self, to_validate: Object) -> None: ...

    def to_dict(self) -> Object:
        return {
            self._name: [item.to_dict() for item in self._items.values()],
        }


## anyOf
class AnyOf(Composition):
    @property
    def _name(self) -> str:
        return "anyOf"

    def __call__(self, to_validate: Object) -> None:
        given: set[str] = set(to_validate.keys())

        intersection: set[str] = self._options & given

        if not intersection:
            raise CompositionError(f"Required: '{self._options}', given was '{given}'")

        for title, item in self._items.items():
            if title in intersection:
                item(to_validate[title])  # type: ignore


## oneOf
class OneOf(Composition):
    @property
    def _name(self) -> str:
        return "oneOf"

    def __call__(self, to_validate: Object) -> None:
        if (n := len(to_validate)) != 1:
            raise CompositionError(
                f"Only one of {self._options} allowed, but {n} {'were' if n != 1 else 'was'} given.",
            )

        given: str = next(iter(to_validate.keys()))

        if given not in self._options:
            raise CompositionError(
                f"'{given}' is not valid. Must be one of {self._options}.",
            )

        self._items[given](to_validate[given])  # type: ignore


## not
class Not(Composition):
    @property
    def _name(self) -> str:
        return "not"

    def __call__(self, to_validate: Object) -> None:
        errors = []

        for title, item in self._items.items():
            validation_failed = False
            error = None

            try:
                item(to_validate)  # type: ignore
            except CompositionError:
                validation_failed = True
            except Exception as e:  # noqa: BLE001
                error = e

            if error is not None:
                raise error

            if not validation_failed:
                errors.append(f"Validation '{title}' should not have passed.")  # type: ignore

        if errors:
            raise CompositionError("; ".join(errors))  # type: ignore
