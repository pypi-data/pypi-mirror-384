from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar, overload

from .core.types import Array, Boolean, Integer, Number, String

if TYPE_CHECKING:
    from specflow.core.schema import Schema

    from .core.types.constraints import Constraint

T = TypeVar("T", str, int, float, bool)


## General Overloads
@overload
def Field(
    title: str,
    type_: Literal["string"],
    description: str | None = None,
    default: str | None = None,
    const: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    enum: list[str] | None = None,
    constraints: list[Constraint[str]] | None = None,
    *,
    nullable: bool = False,
) -> String: ...


@overload
def Field(
    title: str,
    type_: Literal["integer"],
    description: str | None = None,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
    exclusive_minimum: int | None = None,
    exclusive_maximum: int | None = None,
    mult: int | None = None,
    constraints: list[Constraint[int]] | None = None,
    *,
    nullable: bool = False,
) -> Integer: ...


@overload
def Field(
    title: str,
    type_: Literal["number"],
    description: str | None = None,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    exclusive_minimum: float | None = None,
    excluvie_maximum: float | None = None,
    mult: float | None = None,
    constraints: list[Constraint[float]] | None = None,
    *,
    nullable: bool = False,
) -> Number: ...


@overload
def Field(
    title: str,
    type_: Literal["boolean"],
    description: str | None = None,
    constraints: list[Constraint[bool]] | None = None,
    *,
    nullable: bool = False,
    default: bool | None = None,
) -> Boolean: ...


@overload
def Field(
    title: str,
    type_: Literal["array"],
    description: str | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    min_contains: int | None = None,
    max_contains: int | None = None,
    items: String | Number | Integer | Boolean | Schema | None = None,
    prefix_items: list[String | Number | Integer | Boolean | Schema] | None = None,
    *,
    nullable: bool = False,
) -> Array: ...


## String inference - based on string-specific parameters
@overload
def Field(
    title: str,
    description: str | None = None,
    default: str | None = None,
    *,
    const: str,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    enum: list[str] | None = None,
    constraints: list[Constraint[str]] | None = None,
    nullable: bool = False,
) -> String: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: str | None = None,
    const: str | None = None,
    *,
    min_length: int,
    max_length: int | None = None,
    pattern: str | None = None,
    enum: list[str] | None = None,
    constraints: list[Constraint[str]] | None = None,
    nullable: bool = False,
) -> String: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: str | None = None,
    const: str | None = None,
    min_length: int | None = None,
    *,
    max_length: int,
    pattern: str | None = None,
    enum: list[str] | None = None,
    constraints: list[Constraint[str]] | None = None,
    nullable: bool = False,
) -> String: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: str | None = None,
    const: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    *,
    pattern: str,
    enum: list[str] | None = None,
    constraints: list[Constraint[str]] | None = None,
    nullable: bool = False,
) -> String: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: str | None = None,
    const: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    *,
    enum: list[str],
    constraints: list[Constraint[str]] | None = None,
    nullable: bool = False,
) -> String: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    *,
    default: str,
    const: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    enum: list[str] | None = None,
    constraints: list[Constraint[str]] | None = None,
    nullable: bool = False,
) -> String: ...


## Integer inference - based on integer-specific parameters
@overload
def Field(
    title: str,
    description: str | None = None,
    default: int | None = None,
    *,
    minimum: int,
    maximum: int | None = None,
    exclusive_minimum: int | None = None,
    exclusive_maximum: int | None = None,
    mult: int | None = None,
    constraints: list[Constraint[int]] | None = None,
    nullable: bool = False,
) -> Integer: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: int | None = None,
    minimum: int | None = None,
    *,
    maximum: int,
    exclusive_minimum: int | None = None,
    exclusive_maximum: int | None = None,
    mult: int | None = None,
    constraints: list[Constraint[int]] | None = None,
    nullable: bool = False,
) -> Integer: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
    *,
    exclusive_minimum: int,
    exclusive_maximum: int | None = None,
    mult: int | None = None,
    constraints: list[Constraint[int]] | None = None,
    nullable: bool = False,
) -> Integer: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
    exclusive_minimum: int | None = None,
    *,
    exclusive_maximum: int,
    mult: int | None = None,
    constraints: list[Constraint[int]] | None = None,
    nullable: bool = False,
) -> Integer: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
    exclusive_minimum: int | None = None,
    exclusive_maximum: int | None = None,
    *,
    mult: int,
    constraints: list[Constraint[int]] | None = None,
    nullable: bool = False,
) -> Integer: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    *,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
    exclusive_minimum: int | None = None,
    exclusive_maximum: int | None = None,
    mult: int | None = None,
    constraints: list[Constraint[int]] | None = None,
    nullable: bool = False,
) -> Integer: ...


## Number/Float inference - based on float-specific parameters
@overload
def Field(
    title: str,
    description: str | None = None,
    default: float | None = None,
    *,
    minimum: float,
    maximum: float | None = None,
    exclusive_minimum: float | None = None,
    excluvie_maximum: float | None = None,
    mult: float | None = None,
    constraints: list[Constraint[float]] | None = None,
    nullable: bool = False,
) -> Number: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: float | None = None,
    minimum: float | None = None,
    *,
    maximum: float,
    exclusive_minimum: float | None = None,
    excluvie_maximum: float | None = None,
    mult: float | None = None,
    constraints: list[Constraint[float]] | None = None,
    nullable: bool = False,
) -> Number: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    *,
    exclusive_minimum: float,
    excluvie_maximum: float | None = None,
    mult: float | None = None,
    constraints: list[Constraint[float]] | None = None,
    nullable: bool = False,
) -> Number: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    exclusive_minimum: float | None = None,
    *,
    excluvie_maximum: float,
    mult: float | None = None,
    constraints: list[Constraint[float]] | None = None,
    nullable: bool = False,
) -> Number: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    exclusive_minimum: float | None = None,
    excluvie_maximum: float | None = None,
    *,
    mult: float,
    constraints: list[Constraint[float]] | None = None,
    nullable: bool = False,
) -> Number: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    *,
    default: float,
    minimum: float | None = None,
    maximum: float | None = None,
    exclusive_minimum: float | None = None,
    excluvie_maximum: float | None = None,
    mult: float | None = None,
    constraints: list[Constraint[float]] | None = None,
    nullable: bool = False,
) -> Number: ...


## Boolean inference - based on boolean-specific parameters
@overload
def Field(
    title: str,
    description: str | None = None,
    *,
    default: bool,
    constraints: list[Constraint[bool]] | None = None,
    nullable: bool = False,
) -> Boolean: ...


## Array inference - based on array-specific parameters
@overload
def Field(
    title: str,
    description: str | None = None,
    *,
    min_items: int,
    max_items: int | None = None,
    min_contains: int | None = None,
    max_contains: int | None = None,
    items: String | Number | Integer | Boolean | Schema | None = None,
    prefix_items: list[String | Number | Integer | Boolean | Schema] | None = None,
    nullable: bool = False,
) -> Array: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    min_items: int | None = None,
    *,
    max_items: int,
    min_contains: int | None = None,
    max_contains: int | None = None,
    items: String | Number | Integer | Boolean | Schema | None = None,
    prefix_items: list[String | Number | Integer | Boolean | Schema] | None = None,
    nullable: bool = False,
) -> Array: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    *,
    min_contains: int,
    max_contains: int | None = None,
    items: String | Number | Integer | Boolean | Schema | None = None,
    prefix_items: list[String | Number | Integer | Boolean | Schema] | None = None,
    nullable: bool = False,
) -> Array: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    min_contains: int | None = None,
    *,
    max_contains: int,
    items: String | Number | Integer | Boolean | Schema | None = None,
    prefix_items: list[String | Number | Integer | Boolean | Schema] | None = None,
    nullable: bool = False,
) -> Array: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    min_contains: int | None = None,
    max_contains: int | None = None,
    *,
    items: String | Number | Integer | Boolean | Schema,
    prefix_items: list[String | Number | Integer | Boolean | Schema] | None = None,
    nullable: bool = False,
) -> Array: ...


@overload
def Field(
    title: str,
    description: str | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    min_contains: int | None = None,
    max_contains: int | None = None,
    items: String | Number | Integer | Boolean | Schema | None = None,
    *,
    prefix_items: list[String | Number | Integer | Boolean | Schema],
    nullable: bool = False,
) -> Array: ...


## Implementation
def Field(  # noqa: C901, N802, PLR0911 # type: ignore
    title: str,
    type_: Literal["string", "integer", "number", "boolean", "array"] | None = None,
    description: str | None = None,
    default: str | float | bool | None = None,  # noqa: FBT001
    # String specific
    const: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    enum: list[str] | None = None,
    # Integer specific
    minimum: float | None = None,
    maximum: float | None = None,
    exclusive_minimum: float | None = None,
    exclusive_maximum: float | None = None,
    mult: float | None = None,
    # Number specific (uses same params as integer but with float types)
    excluvie_maximum: float | None = None,
    # Array specific
    min_items: int | None = None,
    max_items: int | None = None,
    min_contains: int | None = None,
    max_contains: int | None = None,
    items: String | Number | Integer | Boolean | Schema | None = None,
    prefix_items: list[String | Number | Integer | Boolean | Schema] | None = None,
    # Generic
    constraints: list[Constraint] | None = None,  # type: ignore
    nullable: bool = False,  # noqa: FBT001, FBT002
) -> String | Integer | Number | Boolean | Array:
    # If type is explicitly provided, use it
    if type_ == "string":
        return String(
            title=title,
            description=description,
            default=default,  # type: ignore
            const=const,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            enum=enum,
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )
    if type_ == "integer":
        return Integer(
            title=title,
            description=description,
            default=default,  # type: ignore
            minimum=minimum,  # type: ignore
            maximum=maximum,  # type: ignore
            exclusive_minimum=exclusive_minimum,  # type: ignore
            exclusive_maximum=exclusive_maximum,  # type: ignore
            mult=mult,  # type: ignore
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )
    if type_ == "number":
        return Number(
            title=title,
            description=description,
            default=default,  # type: ignore
            minimum=minimum,  # type: ignore
            maximum=maximum,  # type: ignore
            exclusive_minimum=exclusive_minimum,  # type: ignore
            excluvie_maximum=excluvie_maximum or exclusive_maximum,  # type: ignore
            mult=mult,  # type: ignore
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )
    if type_ == "boolean":
        return Boolean(
            title=title,
            description=description,
            default=default,  # type: ignore
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )
    if type_ == "array":
        return Array(
            title=title,
            description=description,
            min_items=min_items,
            max_items=max_items,
            min_contains=min_contains,
            max_contains=max_contains,
            items=items,
            prefix_items=prefix_items,
            nullable=nullable,
        )

    # Infer type based on parameters provided
    # String-specific parameters
    if any([const, min_length, max_length, pattern, enum]):
        return String(
            title=title,
            description=description,
            default=default,  # type: ignore
            const=const,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            enum=enum,
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )

    # Array-specific parameters
    if any([min_items, max_items, min_contains, max_contains, items, prefix_items]):
        return Array(
            title=title,
            description=description,
            min_items=min_items,
            max_items=max_items,
            min_contains=min_contains,
            max_contains=max_contains,
            items=items,
            prefix_items=prefix_items,
            nullable=nullable,
        )

    # Boolean inference from default
    if isinstance(default, bool):
        return Boolean(
            title=title,
            description=description,
            default=default,
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )

    # String inference from default
    if isinstance(default, str):
        return String(
            title=title,
            description=description,
            default=default,
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )

    # Check if parameters suggest float (Number) vs int (Integer)
    # If any parameter is explicitly a float, use Number
    has_float_values = any(
        isinstance(val, float)
        for val in [  # type: ignore
            default,
            minimum,
            maximum,
            exclusive_minimum,
            exclusive_maximum,
            excluvie_maximum,
            mult,
        ]
        if val is not None
    )

    has_numeric_constraints = any(
        [
            minimum is not None,
            maximum is not None,
            exclusive_minimum is not None,
            exclusive_maximum is not None,
            excluvie_maximum is not None,
            mult is not None,
        ],
    )

    # If we have float values, infer Number
    if has_float_values:
        return Number(
            title=title,
            description=description,
            default=default,  # type: ignore
            minimum=minimum,  # type: ignore
            maximum=maximum,  # type: ignore
            exclusive_minimum=exclusive_minimum,  # type: ignore
            excluvie_maximum=excluvie_maximum or exclusive_maximum,  # type: ignore
            mult=mult,  # type: ignore
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )

    # If we have an integer default, infer Integer
    if isinstance(default, int):
        return Integer(
            title=title,
            description=description,
            default=default,  # type: ignore
            minimum=minimum,  # type: ignore
            maximum=maximum,  # type: ignore
            exclusive_minimum=exclusive_minimum,  # type: ignore
            exclusive_maximum=exclusive_maximum,  # type: ignore
            mult=mult,  # type: ignore
            constraints=constraints,  # type: ignore
            nullable=nullable,
        )

    # If we have numeric constraints but no clear type indicator, this is ambiguous
    if has_numeric_constraints:
        raise ValueError(
            f"Cannot infer type for field '{title}'. "
            f"Numeric constraints (minimum, maximum, etc.) are ambiguous without a default value or explicit type_. "
            f"Please provide either:\n"
            f"  - A default value with the appropriate type (int or float)\n"
            f"  - An explicit type_ parameter ('integer' or 'number')",
        )

    # If we reach here with only title/description/constraints, this is ambiguous
    raise ValueError(
        f"Cannot infer type for field '{title}'. "
        f"Please specify type_ parameter or provide type-specific parameters such as:\n"
        f"  - For String: min_length, max_length, pattern, enum, const, or a str default\n"
        f"  - For Integer: minimum, maximum, mult with an int default\n"
        f"  - For Number: minimum, maximum, mult with a float default\n"
        f"  - For Boolean: a bool default\n"
        f"  - For Array: min_items, max_items, items, prefix_items",
    )
