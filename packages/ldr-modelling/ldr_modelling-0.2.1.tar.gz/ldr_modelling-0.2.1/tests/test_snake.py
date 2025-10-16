# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Test the `ldr.modelling.snake.Model` class."""

from __future__ import annotations

from ldr.modelling import snake


class Person(snake.Model):
    """A person."""

    firstName: str  # noqa: N815
    lastName: str  # noqa: N815


def test_camel_case_base_model_instantiates_from_alias() -> None:
    """Test the CamelCaseBaseModel class."""
    data = {
        "first_name": "John",
        "last_name": "Smith",
    }

    person = Person.model_validate(data)

    assert person.firstName == data["first_name"]
    assert person.lastName == data["last_name"]


def test_camel_case_base_model_serializes_to_alias() -> None:
    """Test the CamelCaseBaseModel class."""
    data = {
        "first_name": "John",
        "last_name": "Smith",
    }

    person = Person.model_validate(data)

    assert person.model_dump(by_alias=True) == data
