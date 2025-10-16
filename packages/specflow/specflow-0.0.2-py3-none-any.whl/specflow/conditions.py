from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._typing import JSON
    from .schema import Schema
    from .types import Type


class ConditionError(Exception): ...


class Condition:
    def __init__(
        self,
        if_: Schema | Type,
        then_: Schema | Type,
        else_: Schema | Type | None = None,
    ) -> None:
        """1.	if: Defines the condition to test against the data
        2.	then: Applied when if validates successfully
        3.	else: Applied when if fails validation (optional).
        """
        self._if: Schema | Type = if_
        self._else: Schema | Type = else_
        self._then: Schema | Type | None = then_

    def __call__(self, to_validate: JSON) -> None:
        if (if_title := self._if.title) not in to_validate:
            raise ConditionError(
                f"Required condition field '{if_title}' not found in data",
            )

        try:
            self._if(to_validate[if_title])
            self._then(to_validate[self._then.title])
        except Exception as e:
            if self._else and (else_title := self._else.title in to_validate):
                self._then(to_validate[else_title])
            else:
                raise ConditionError(
                    f"Condition validation failed and no valid else branch available: {e!s}",
                )

    def to_dict(self) -> JSON:
        data: JSON = {"if": self._if.to_dict()}

        if self._else:
            data["else"] = self._else.to_dict()

        if self._then:
            data["then"] = self._then.to_dict()

        return data
