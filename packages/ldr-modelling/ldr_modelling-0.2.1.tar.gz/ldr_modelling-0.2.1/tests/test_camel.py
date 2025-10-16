# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Test the `ldr.modelling.camel.Model` class."""

from __future__ import annotations

from ldr.modelling import camel


class Person(camel.Model):
    """A person."""

    first_name: str
    last_name: str


def test_camel_case_base_model_instantiates_from_alias() -> None:
    """Test the CamelCaseBaseModel class."""
    data = {
        "firstName": "John",
        "lastName": "Smith",
    }

    person = Person.model_validate(data)

    assert person.first_name == data["firstName"]
    assert person.last_name == data["lastName"]


def test_camel_case_base_model_serializes_to_alias() -> None:
    """Test the CamelCaseBaseModel class."""
    data = {
        "firstName": "John",
        "lastName": "Smith",
    }

    person = Person.model_validate(data)

    assert person.model_dump(by_alias=True) == data
