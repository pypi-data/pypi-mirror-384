from __future__ import annotations

from typing import TypeAlias, TypeVar

T = TypeVar("T")
E = TypeVar("E")


JSONValue: TypeAlias = (
    str | int | float | bool | None | dict[str, "JSONValue"] | list["JSONValue"]
)
JSON: TypeAlias = dict[str, JSONValue]
