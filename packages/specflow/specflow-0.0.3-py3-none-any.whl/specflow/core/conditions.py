from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specflow.typing import Object

    from .schema import Schema
    from .types import Boolean, Integer, Number, String


class ConditionError(Exception): ...


class Condition:
    def __init__(
        self,
        if_: Schema | String | Number | Integer | Boolean,
        then_: Schema | String | Number | Integer | Boolean,
        else_: Schema | String | Number | Integer | Boolean | None = None,
    ) -> None:
        self._if: Schema | String | Number | Integer | Boolean = if_
        self._else: Schema | String | Number | Integer | Boolean | None = else_
        self._then: Schema | String | Number | Integer | Boolean | None = then_

    def __call__(self, to_validate: Object) -> None:
        if (if_title := self._if.title) not in to_validate:
            raise ConditionError(
                f"Required condition field '{if_title}' not found in data",
            )

        try:
            self._if(to_validate[if_title])  # type: ignore
            self._then(to_validate[self._then.title])  # type: ignore
        except Exception as e:  # noqa: BLE001
            if self._else and (else_title := self._else.title in to_validate):
                self._then(to_validate[else_title])  # type: ignore
            else:
                raise ConditionError(  # noqa: B904
                    f"Condition validation failed and no valid else branch available: {e!s}",
                )

    def to_dict(self) -> Object:
        data: Object = {"if": self._if.to_dict()}

        if self._else:
            data["else"] = self._else.to_dict()

        if self._then:
            data["then"] = self._then.to_dict()

        return data
