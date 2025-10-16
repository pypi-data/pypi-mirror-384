from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._typing import JSON
    from .constraints import Constraint
    from .schema import Schema
    from .types import Type


class Array:
    def __init__(
        self,
        title: str,
        description: str | None = None,
        items: Type | Schema | None = None,
        prefixItems: list[Type | Schema] | None = None,
        constraints: Sequence[Constraint] | None = None,
    ) -> None:
        self._title: str = title
        self._description: str | None = description
        self._items: Type | Schema | None = items
        self._prefix_items: list[Type | Schema] | None = prefixItems
        self._constraints: Sequence[Constraint] | None = constraints

    @property
    def title(self) -> str:
        return self._title

    def _validate_items(self, to_validate: list) -> None:
        """Validate array constraints (minItems, maxItems, etc.)"""
        if self._constraints:
            for constraint in self._constraints:
                constraint(to_validate)

    def _validate_item_schemas(self, to_validate: list) -> None:
        """Validate individual items against their schemas"""
        # If prefixItems is defined, validate positional items
        if self._prefix_items:
            for i, (item_schema, item_value) in enumerate(
                zip(self._prefix_items, to_validate, strict=False),
            ):
                try:
                    item_schema(item_value)
                except Exception as e:
                    raise ValueError(
                        f"Item at index {i} failed validation: {e}",
                    ) from e

            # If there are extra items beyond prefixItems, validate with items schema
            if len(to_validate) > len(self._prefix_items) and self._items:
                for i in range(len(self._prefix_items), len(to_validate)):
                    try:
                        self._items(to_validate[i])
                    except Exception as e:
                        raise ValueError(
                            f"Item at index {i} failed validation: {e}",
                        ) from e

        # If only items is defined (no prefixItems), validate all items with same schema
        elif self._items:
            for i, item_value in enumerate(to_validate):
                try:
                    self._items(item_value)
                except Exception as e:
                    raise ValueError(
                        f"Item at index {i} failed validation: {e}",
                    ) from e

    def __call__(self, to_validate: list) -> None:
        if not isinstance(to_validate, list):
            raise TypeError(f"Expected list, got {type(to_validate).__name__}")

        # First validate array-level constraints (length, etc.)
        self._validate_items(to_validate)

        # Then validate individual item schemas
        self._validate_item_schemas(to_validate)

    def to_dict(self) -> JSON:
        data: JSON = {
            self._title: {
                "type": "array",
            },
        }

        inner_data = data[self._title]

        if self._description is not None:
            inner_data["description"] = self._description

        if self._items:
            inner_data["items"] = self._items.to_dict()

        if self._prefix_items:
            inner_data["prefixItems"] = [item.to_dict() for item in self._prefix_items]

        # Add constraints to the schema
        if self._constraints:
            for constraint in self._constraints:
                inner_data.update(constraint.to_dict())

        return data
