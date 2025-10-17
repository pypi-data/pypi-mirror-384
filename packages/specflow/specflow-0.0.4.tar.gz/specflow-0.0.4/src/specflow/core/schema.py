from __future__ import annotations

from typing import TYPE_CHECKING

from .types import Boolean, Integer, Number, String
from .types.array import Array

if TYPE_CHECKING:
    from specflow.core.compositions import Composition
    from specflow.core.conditions import Condition
    from specflow.typing import Object


class Schema:
    def __init__(
        self,
        title: str,
        properties: list[
            String | Number | Integer | Boolean | Composition | Schema | Array
        ],
        conditions: list[Condition] | None = None,
        description: str | None = None,
    ) -> None:
        if not properties:
            raise ValueError("'properties' can't be empty.")

        self._title: str = title
        self._items: dict[
            str,
            String | Number | Integer | Boolean | Schema | Array,
        ] = {}
        self._compositions: list[Composition] = []
        self._conditions: list[Condition] | None = conditions
        self._description: str | None = description
        self._properties: list[
            String | Number | Integer | Boolean | Composition | Array | Schema
        ] = properties

        for property_ in properties:
            if isinstance(
                property_,
                (String | Number | Integer | Boolean, Schema, Array),
            ):
                self._items[property_.title] = property_
            else:
                self._compositions.append(property_)

        self._required: set[str] = set(self._items.keys())

    @property
    def title(self) -> str:
        return self._title

    def __call__(self, to_validate: Object) -> None:
        given: set[str] = set(to_validate.keys())

        missing: set[str] = self._required - given

        if missing:
            missing_fields = "', '".join(sorted(missing))
            if len(missing) == 1:
                raise TypeError(
                    f"Schema '{self._title}' is missing required field: '{missing_fields}'",
                )
            raise TypeError(
                f"Schema '{self._title}' is missing {len(missing)} required fields: '{missing_fields}'",
            )

        for title, fn in self._items.items():
            fn(to_validate[title])  # type: ignore

        for composition in self._compositions:
            composition(to_validate)

        if self._conditions:
            for condition in self._conditions:
                condition(to_validate)

    def to_dict(self) -> Object:
        data: Object = {
            "title": self._title,
            "description": self._description,
            "properties": [property_.to_dict() for property_ in self._properties],  # type: ignore
        }

        if self._conditions:
            return data | {
                "conditions": [condition.to_dict() for condition in self._conditions],  # type: ignore
            }

        return data
