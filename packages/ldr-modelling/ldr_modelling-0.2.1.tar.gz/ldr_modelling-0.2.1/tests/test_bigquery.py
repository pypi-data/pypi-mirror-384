# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Test the bigquery.Model class."""

from __future__ import annotations

import datetime
import typing

import orjson
import pydantic
import pytest
from ldr.modelling.bigquery import errors, model, types

State = typing.Literal["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]


class Address(model.Model):
    """An address."""

    street: str
    city: str
    state: State
    post_code: int = pydantic.Field(
        description="The Australian postal code (0000-9999).",
    )


class Interest(model.Model):
    """A person's interest."""

    name: str
    description: str | None


class Person(model.Model):
    """A person."""

    name: str
    age: int
    height: float | None = pydantic.Field(
        description="The height of the person in centimeters.",
    )
    address: Address
    interests: list[Interest] = pydantic.Field(
        description="The person's interests.",
    )
    created_at: datetime.datetime = pydantic.Field(
        description="The date and time the record was created.",
    )
    date_of_birth: datetime.date | None = pydantic.Field(
        description="The date of birth of the person.",
    )
    metadata: dict[str, str] | None = pydantic.Field(
        description="Metadata about the person.",
    )
    active: bool
    some_time_field: datetime.time
    repeated_strings: list[str]
    another_timestamp: typing.Annotated[types.Timestamp, types.TimestampValidator]
    geo: typing.Annotated[types.Geography, types.GeographyValidator]


PERSON_SCHEMA = [
    {
        "name": "name",
        "type": "STRING",
        "mode": "REQUIRED",
    },
    {
        "name": "age",
        "type": "INTEGER",
        "mode": "REQUIRED",
    },
    {
        "name": "height",
        "type": "FLOAT",
        "mode": "NULLABLE",
        "description": "The height of the person in centimeters.",
    },
    {
        "name": "address",
        "type": "RECORD",
        "mode": "REQUIRED",
        "fields": [
            {
                "name": "street",
                "type": "STRING",
                "mode": "REQUIRED",
            },
            {
                "name": "city",
                "type": "STRING",
                "mode": "REQUIRED",
            },
            {
                "name": "state",
                "type": "STRING",
                "mode": "REQUIRED",
            },
            {
                "name": "post_code",
                "type": "INTEGER",
                "mode": "REQUIRED",
                "description": "The Australian postal code (0000-9999).",
            },
        ],
    },
    {
        "name": "interests",
        "type": "RECORD",
        "mode": "REPEATED",
        "fields": [
            {
                "name": "name",
                "type": "STRING",
                "mode": "REQUIRED",
            },
            {
                "name": "description",
                "type": "STRING",
                "mode": "NULLABLE",
            },
        ],
        "description": "The person's interests.",
    },
    {
        "name": "created_at",
        "type": "DATETIME",
        "mode": "REQUIRED",
        "description": "The date and time the record was created.",
    },
    {
        "name": "date_of_birth",
        "type": "DATE",
        "mode": "NULLABLE",
        "description": "The date of birth of the person.",
    },
    {
        "name": "metadata",
        "type": "JSON",
        "mode": "NULLABLE",
        "description": "Metadata about the person.",
    },
    {
        "name": "active",
        "type": "BOOLEAN",
        "mode": "REQUIRED",
    },
    {
        "name": "some_time_field",
        "type": "TIME",
        "mode": "REQUIRED",
    },
    {
        "name": "repeated_strings",
        "type": "STRING",
        "mode": "REPEATED",
    },
    {
        "name": "another_timestamp",
        "type": "TIMESTAMP",
        "mode": "REQUIRED",
    },
    {
        "name": "geo",
        "type": "GEOGRAPHY",
        "mode": "REQUIRED",
    },
]


def test_bq_base_model_to_bigquery_schema() -> None:
    """Test the to_model_schema method."""
    assert Person.to_bigquery_schema_dict() == PERSON_SCHEMA


def test_bq_base_model_raises_with_none() -> None:
    """Test that the model throws with an annotated None."""

    class _Example(model.Model):
        test: None

    with pytest.raises(model.InvalidTypeError):
        _Example.to_bigquery_schema()


def test_bq_base_model_to_bigquery_schema_ser() -> None:
    """Test passing serialization arguments."""

    class _Example(model.Model):
        name: str

    assert (
        _Example.to_bigquery_schema_ser(serializer=orjson.dumps)
        == b'[{"name":"name","type":"STRING","mode":"REQUIRED"}]'
    )


def test_bq_base_model_raises_with_unsupported_union() -> None:
    """Test that the model throws with an unsupported union."""

    class Example(model.Model):
        """A test model."""

        test: str | int

    with pytest.raises(model.UnsupportedTypeError):
        Example.to_bigquery_schema()


def test__union_types_is_valid() -> None:
    """Test that the _union_types_is_valid method."""
    assert model._union_types_is_valid(str | int) is False
    assert model._union_types_is_valid(str | int | None) is False
    assert model._union_types_is_valid(str | None) is True


def test__get_builtin_field_type() -> None:
    """Test the _get_builtin_field_type raises when given an unsupported type."""
    with pytest.raises(model.InvalidTypeError):
        model._get_flat_field_type(list)

    with pytest.raises(model.InvalidTypeError):
        model._get_flat_field_type(dict)


def test__get_field_type() -> None:
    """Test the _get_field_type method."""
    assert model._get_field_type(str) == "STRING"
    assert model._get_field_type(int) == "INTEGER"
    assert model._get_field_type(float) == "FLOAT"
    assert model._get_field_type(bool) == "BOOLEAN"
    assert model._get_field_type(list[str]) == "STRING"
    assert model._get_field_type(set[int]) == "INTEGER"
    assert model._get_field_type(dict[str, str]) == "JSON"
    assert model._get_field_type(datetime.datetime) == "DATETIME"
    assert model._get_field_type(datetime.date) == "DATE"
    assert model._get_field_type(str | None) == "STRING"
    assert model._get_field_type(datetime.time) == "TIME"

    with pytest.raises(errors.InvalidTypeError):
        model._get_field_type(None)

    with pytest.raises(errors.InvalidTypeError):
        model._get_field_type(list)

    with pytest.raises(errors.InvalidTypeError):
        model._get_field_type(dict)

    with pytest.raises(errors.UnsupportedTypeError):
        model._get_field_type(tuple)

    with pytest.raises(errors.UnsupportedTypeError):
        model._get_field_type(tuple[str])


def test__get_field_mode() -> None:
    """Test the _get_field_mode method."""
    assert model._get_field_mode(None) == "NULLABLE"
    assert model._get_field_mode(type(None)) == "NULLABLE"
    assert model._get_field_mode(str) == "REQUIRED"
    assert model._get_field_mode(str | None) == "NULLABLE"
    assert model._get_field_mode(list[str]) == "REPEATED"
    assert model._get_field_mode(dict[str, str]) == "REQUIRED"
    assert model._get_field_mode(dict[str, str] | None) == "NULLABLE"

    with pytest.raises(model.UnsupportedTypeError):
        model._get_field_mode(str | int)

    with pytest.raises(model.UnsupportedTypeError):
        model._get_field_mode(tuple[str])


def test__get_field_name_with_alias() -> None:
    """Test the _get_field_mode_method."""
    assert (
        model._get_field_name(
            "street_address",
            pydantic.Field(alias="streetAddress"),
            by_alias=True,
        )
        == "streetAddress"
    )


def test__get_field_name_with_serialization_alias() -> None:
    """Test the _get_field_mode_method."""
    assert (
        model._get_field_name(
            "street_address",
            pydantic.Field(serialization_alias="streetAddress"),
            by_alias=True,
        )
        == "streetAddress"
    )


def test__get_field_name_with_no_alias() -> None:
    """Test the _get_field_mode_method."""
    with pytest.raises(model.MissingAliasError):
        model._get_field_name(
            "street_address",
            pydantic.Field(),
            by_alias=True,
        )
