from __future__ import annotations

from .type import Type


class Boolean(Type[bool]):
    @property
    def _type(self) -> str:
        return "boolean"
