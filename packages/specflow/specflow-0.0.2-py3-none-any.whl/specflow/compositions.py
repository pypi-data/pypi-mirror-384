from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._typing import JSON
    from .schema import Schema
    from .types import Type


## Base
class CompositionError(Exception): ...


class Composition(ABC):
    def __init__(
        self,
        *items: Schema | Type,
    ) -> None:
        if not items:
            raise ValueError("'items' cannot be empty.")

        self._items: tuple[Schema | Type, ...] = {item.title: item for item in items}

        self._options: set[str] = set(self._items.keys())

    @property
    @abstractmethod
    def _name(self) -> str: ...

    @abstractmethod
    def __call__(self, to_validate: JSON) -> None: ...

    def to_dict(self) -> JSON:
        return {
            self._name: [item.to_dict() for item in self._items],
        }


## anyOf
class AnyOf(Composition):
    @property
    def _name(self) -> str:
        return "anyOf"

    def __call__(self, to_validate: dict) -> None:
        given: set[str] = set(to_validate.keys())

        intersection: set[str] = self._options & given

        if not intersection:
            raise CompositionError(f"Required: '{self._options}', given was '{given}'")

        for title, fn in self._items.items():
            if title in intersection:
                fn(to_validate[title])


## oneOf
class OneOf(Composition):
    @property
    def _name(self) -> str:
        return "oneOf"

    def __call__(self, to_validate: dict) -> None:
        if (n := len(to_validate)) != 1:
            raise CompositionError(
                f"Only one of {self._options} allowed, but {n} {'were' if n != 1 else 'was'} given.",
            )

        given: str = list(to_validate.keys())[0]

        if given not in self._options:
            raise CompositionError(
                f"'{given}' is not valid. Must be one of {self._options}.",
            )

        self._items[given](to_validate[given])


## not
class Not(Composition):
    @property
    def _name(self) -> str:
        return "not"

    def __call__(self, to_validate: JSON) -> None:
        for title, fn in self._items.items():
            try:
                fn(to_validate)
            except CompositionError:
                pass
            else:
                raise CompositionError(f"Validation '{title}' should not have passed.")
