# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Module for converting models into BigQuery schemas and rows."""

from __future__ import annotations

import datetime
import enum
import json
import types
import typing

import pydantic

_VALID_ARGS_LEN = 2
_TYPE_TO_BQ: dict[type, FieldType] = {
    bytes: "BYTES",
    str: "STRING",
    int: "INTEGER",
    float: "FLOAT",
    bool: "BOOLEAN",
    datetime.datetime: "DATETIME",
    datetime.date: "DATE",
    datetime.time: "TIME",
}


class Field(pydantic.BaseModel):
    """A field in a BigQuery schema."""

    name: str
    type: FieldType
    mode: FieldMode = "NULLABLE"
    description: str | None = None
    fields: list[Field] | None = None

    @classmethod
    def _from_pydantic_field_info(
        cls,
        name: str,
        field: pydantic.fields.FieldInfo,
        *,
        by_alias: bool,
    ) -> Field:
        """
        Convert a model field to a valid BigQuery schema.

        Supports nested models and lists of models, as well
        as optional fields, and `pydantic.Field` descriptions.

        Params
        ------
        by_alias: Whether to use the alias of the field as the name
                  in the schema. Defaults to `False`.

        Returns
        -------
        The BigQuery schema deserialised into python builtins.

        Raises
        ------
        MissingAnnotationError: If a field has no annotation, or the annotation is None.
        InvalidTypeError: If a Model field is determined to be `RECORD` but is
                          not another `Model` subclass.

        """
        if not field.annotation:
            raise MissingAnnotationError(f"Field {name} does not have an annotation")

        f_name = _get_field_name(name, field, by_alias=by_alias)
        f_type = _get_field_type(field.annotation)
        f_mode = _get_field_mode(field.annotation)

        fields: list[Field] | None = None

        # If the field type is another Model, check
        # if it's a list of models or a single model.
        if f_type == "RECORD":
            # If the field is a list of models, get the
            # schema for the model from it's annotation.
            if f_mode == "REPEATED":
                args = typing.get_args(field.annotation)
                if not args and not isinstance(Model, args[0]):
                    raise InvalidTypeError

                fields = args[0].to_bigquery_schema(by_alias=by_alias)

            # Else we can get the schema directly.
            else:
                if not issubclass(field.annotation, Model):
                    raise InvalidTypeError

                fields = field.annotation.to_bigquery_schema(by_alias=by_alias)

        return cls(
            name=f_name,
            type=f_type,
            mode=f_mode,
            description=field.description,
            fields=fields,
        )


FieldType = typing.Literal[
    "BYTES",
    "STRING",
    "INTEGER",
    "FLOAT",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "JSON",
    "RECORD",
    "TIME",
    # Should also consider how to serialise the following in the future:
    # TIMESTAMP
    # NUMERIC
    # BIGNUMERIC
    # GEOGRAPHY
    #
    # Could lean on numpy types for NUMERIC and BIGNUMERIC.
    # GEOGRAPHY could be an included wrapper on string with
    # a validation check.
]
FieldMode = typing.Literal["REPEATED", "REQUIRED", "NULLABLE"]


class UnsupportedTypeError(ValueError):
    """An annotated type is not representable in BigQuery."""


class InvalidTypeError(TypeError):
    """A Literal annotation is invalid."""


class MissingAnnotationError(InvalidTypeError):
    """A field has no type annotation."""


class MissingAliasError(InvalidTypeError):
    """A field has no alias set."""


class Model(pydantic.BaseModel):
    """Pydantic extension methods to generate BigQuery schemas from models."""

    # Classmethod because we don't need an instance of the model to get the fields.
    @classmethod
    def to_bigquery_schema(cls, *, by_alias: bool = False) -> list[Field]:
        """
        Convert the model to a valid BigQuery schema.

        Supports nested models and lists of models, as well
        as optional fields, and `pydantic.Field` descriptions.

        Params
        ------
        by_alias: Whether to use the alias of the field as the name
                  in the schema. Defaults to `False`.

        Returns
        -------
        The BigQuery schema deserialised into python builtins.

        """
        return [
            Field._from_pydantic_field_info(  # noqa: SLF001
                name,
                field,
                by_alias=by_alias,
            )
            for name, field in cls.model_fields.items()
        ]

    @classmethod
    def to_bigquery_schema_dict(
        cls,
        *,
        by_alias: bool = False,
    ) -> list[dict[str, typing.Any]]:
        """
        Convert the model to a valid BigQuery schema in the form of a python dict.

        Supports nested models and lists of models, as well
        as optional fields, and `pydantic.Field` descriptions.

        Params
        ------
        by_alias: Whether to use the alias of the field as the name
                  in the schema. Defaults to `False`.

        Returns
        -------
        The BigQuery schema deserialised into python builtins.

        """
        return [
            field.model_dump(mode="json", exclude_none=True)
            for field in cls.to_bigquery_schema(by_alias=by_alias)
        ]

    @classmethod
    def to_bigquery_schema_ser[
        **P,
        R,
    ](
        cls,
        by_alias: bool = False,  # noqa: FBT001, FBT002
        serializer: typing.Callable[
            typing.Concatenate[list[dict[str, typing.Any]], P],
            R,
        ] = json.dumps,
        *serializer_args: P.args,
        **serializer_kwargs: P.kwargs,
    ) -> R:
        """
        Convert the model to a valid BigQuery schema and serialize it.

        Defaults to the standard libaray `json.dumps` method, but will
        support any function that can take a `list[dict[str, Any]]`
        and return whatever that serialiser returns.

        Params
        ------
        by_alias: Whether to use the alias of the field as the name
                  in the schema. Defaults to `False`.
        serializer: The callable used to serialize the schema. Defaults to
                    the standard library `json.dumps`.
        serializer_args: Any positional arguments to pass to the serializer callable.
        serializer_kwargs: Any keyword arguments to pass to the serializer callable.

        Returns
        -------
        The serialized BigQuery schema.

        """
        return serializer(
            cls.to_bigquery_schema_dict(by_alias=by_alias),
            *serializer_args,
            **serializer_kwargs,
        )


def _union_types_is_valid(field: types.UnionType) -> bool:
    """
    Check if a union type is supported by BigQuery.

    Returns
    -------
    Whether the union is valid.

    """
    if len(field.__args__) != _VALID_ARGS_LEN:
        return False

    return field.__args__[1] is type(None)


def _get_flat_field_type(field: type) -> FieldType | None:
    """
    Get the BigQuery type for a given builtin annotation.

    Returns
    -------
    The equivelant BigQuery type for a python builtin.

    Raises
    ------
    InvalidTypeError: If a generic type is provided without type information,
                      e.g, `list` provided instead of `list[str]`.

    """
    if field is list:
        raise InvalidTypeError("Please provide a list type, e.g. list[str]")

    if field is dict:
        raise InvalidTypeError("Please provide a dict type, e.g. dict[str, str]")

    return _TYPE_TO_BQ.get(field)


def _get_field_type(field: type | types.UnionType | None) -> FieldType:
    """
    Get the BigQuery type for a python type.

    Returns
    -------
    The equivelant BigQuery type.

    Raises
    ------
    MissingAnnotationError: If a model field does not have a type annotation.
    UnsupportedTypeError: When an invalid or unsupported annotation is provided.

    """
    origin_to_bq: dict[typing.Any, typing.Callable[[type], FieldType]] = {
        list: lambda field: _get_field_type(typing.get_args(field)[0]),
        set: lambda field: _get_field_type(typing.get_args(field)[0]),
        dict: lambda _: "JSON",
        typing.Literal: _get_literal_type,
    }

    if field is type(None) or field is None:
        raise MissingAnnotationError(
            "Please provide a type annotation, e.g. `fieldname: str`",
        )

    origin = typing.get_origin(field)
    args = typing.get_args(field)

    if isinstance(field, types.UnionType):
        if not _union_types_is_valid(field):
            raise UnsupportedTypeError(
                f"Unsupported union type: {field}. Only Union[T, None] is supported.",
            )
        return _get_field_type(args[0])

    if (flat_field := _get_flat_field_type(field)) is not None:
        return flat_field

    if (handler := origin_to_bq.get(origin)) is not None:
        return handler(field)

    if isinstance(field, type):
        if issubclass(field, Model):
            return "RECORD"

        if issubclass(field, enum.Enum):
            return _get_enum_type(field)

    raise UnsupportedTypeError(f"Unsupported field type: {field}")


def _get_literal_type(field: type) -> FieldType:
    """
    Get the field type derived from a `Literal` expression.

    Params
    ------
    field: The type to parse.

    Returns
    -------
    The equivelant BigQuery FieldType.

    Raises
    ------
    InvalidTypeError: If an invalid Literal expression is provided, or if a Literal
                      of multiple types is provided.
    UnsupportedTypeError: If the Literal contains `None` as an expression. In this case,
                          use `Literal[...] | None` instead.

    """
    args = typing.get_args(field)
    if not args:
        raise InvalidTypeError("typing.Literal must not be empty.")
    first_arg_type = type(args[0])

    if not all(isinstance(arg, first_arg_type) for arg in args):
        raise InvalidTypeError(
            "All arguments in a typing.Literal must be of the same "
            "primitive type for BigQuery conversion.",
        )
    bq_type = _get_field_type(first_arg_type)

    if bq_type is None:
        raise UnsupportedTypeError(
            f"Unsupported type in typing.Literal: {first_arg_type}. ",
        )

    return bq_type


def _get_enum_type(field: type[enum.Enum]) -> FieldType:
    member_types: list[type] = [
        type(member.value) for member in field.__members__.values()
    ]

    if len(member_types) == 0:
        raise InvalidTypeError(f"Recieved enum with no members: {field.__qualname__}")

    first_member_type = member_types[0]

    if not all(first_member_type is member for member in member_types):
        raise UnsupportedTypeError(
            f"Recieved enum with mixed member types: {field.__qualname__}",
        )

    return _get_field_type(first_member_type)


def _get_field_mode(field: type | types.UnionType | None) -> FieldMode:
    """
    Get the BigQuery mode for a given field.

    Returns
    -------
    The BigQuery field mode.

    Raises
    ------
    UnsupportedTypeError: If an invalid union type or generic alias is provided.

    """
    if field is type(None) or field is None:
        return "NULLABLE"

    if isinstance(field, types.UnionType):
        if not _union_types_is_valid(field):
            raise UnsupportedTypeError(
                f"Unsupported union type: {field}. Only Union[T, None] is supported.",
            )

        return "NULLABLE"

    if isinstance(field, types.GenericAlias):
        origin = typing.get_origin(field)
        if origin in {list, set}:
            return "REPEATED"

        # Dict is valid for JSON but could be nullable if is provided
        # as a union type, e.g `dict[str, str] | None`. In this case
        # the above check for `types.UnionType` will catch it.
        # so we can assume it's required, just to make sure we aren't
        # invalidating dict when it is a required field.
        if origin is dict:
            return "REQUIRED"

        # Don't care about stuff like `tuple` so raise
        # an error here. Could look into converting iterables to a list
        # and mappings to a dict down the road using `abc` module?
        raise UnsupportedTypeError(f"Unsupported generic alias: {field}")

    return "REQUIRED"


def _get_field_name(
    name: str,
    field: pydantic.fields.FieldInfo,
    *,
    by_alias: bool,
) -> str:
    """
    Get the correct field name for the BigQuery schema.

    Params
    ------
    name: The actual name of the field as declared on the model. Used as a fallback.
    field: The pydantic FieldInfo for the field.
    by_alias: Whether to use the `alias` or `serialization_alias` in the table name.

    Returns
    -------
    The field name to use.

    Raises
    ------
    MissingAliasError: If no alias is present when using `by_alias`.

    """
    if by_alias:
        if field.alias is None and field.serialization_alias is None:
            raise MissingAliasError(
                f"No alias found for field {name}. Please provide `model_config` "
                "to your class, inherit from a pre-configured class, or manually "
                "set an alias using `pydantic.Field`",
            )

        if field.alias:
            return field.alias
        if field.serialization_alias:
            return field.serialization_alias

    return name
