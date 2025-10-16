from __future__ import annotations

from typing import TYPE_CHECKING

from .compositions import Composition
from .types import Type

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .conditions import Condition


class Schema:
    def __init__(
        self,
        title: str,
        properties: Sequence[Type | Composition | Schema],
        conditions: Sequence[Condition] | None = None,
        description: str | None = None,
    ) -> None:
        if not properties:
            raise ValueError("'properties' can't be empty.")

        self._title: str = title
        self._items: dict[str, Type | Schema] = {}
        self._compositions: list[Composition] = []
        self._conditions: Sequence[Condition] = conditions

        for property in properties:
            if isinstance(property, (Type, Schema)):
                self._items[property.title] = property
            elif isinstance(property, Composition):
                self._compositions.append(property)

        self._required: set[str] = set(self._items.keys())

    @property
    def title(self) -> str:
        return self._title

    def __call__(self, to_validate: dict) -> None:
        given: set[str] = set(to_validate.keys())

        missing: set[str] = self._required - given

        if missing:
            # TODO: correct error
            raise TypeError(f"Missing '{missing}'")
        for title, fn in self._items.items():
            fn(to_validate[title])

        for composition in self._compositions:
            composition(to_validate)

        if self._conditions:
            for condition in self._conditions:
                condition(to_validate)

    def to_dict(self) -> dict:
        data = {
            "title": self.title,
            "properties": [property.to_dict() for property in self._properties],
        }

        if self._conditions:
            return data | {
                "conditions": [condition.to_dict() for condition in self._conditions],
            }

        return data
