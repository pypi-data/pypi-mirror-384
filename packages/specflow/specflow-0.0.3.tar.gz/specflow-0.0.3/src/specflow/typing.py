from __future__ import annotations

from typing import TypeAlias

Value: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | list[str]
    | list[int]
    | list[float]
    | list[bool]
    | list[None]
    | list["Object"]
)
Object: TypeAlias = dict[
    str,
    str
    | int
    | float
    | bool
    | None
    | list[str]
    | list[int]
    | list[float]
    | list[bool]
    | list[None]
    | list["Object"]
    | dict[str, "Object"]
    | "Object",  # type: ignore  # noqa: TC010
]
