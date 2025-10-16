# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Test the bigquery.types.Numeric validator."""

from __future__ import annotations

import typing
from decimal import Decimal

from ldr.modelling import bigquery
from ldr.modelling.bigquery.types import Numeric, NumericValidator  # noqa: TCH002


class _Model(bigquery.Model):
    numeric: typing.Annotated[Numeric, NumericValidator]


def test_numeric_string_validation() -> None:
    """Ensure a string format point is parsed correctly."""
    value = "0.91"
    assert _Model.model_validate({"numeric": value}).numeric == Decimal(value)


def test_numeric_float_validation() -> None:
    """Ensure a bytes format point is parsed correctly."""
    value = 1234.5678
    assert _Model.model_validate({"numeric": value}).numeric == Decimal(str(value))


def test_numeric_to_bq_schema() -> None:
    """Ensure the model field dumps as numeric."""
    assert _Model.to_bigquery_schema_dict() == [
        {
            "name": "numeric",
            "type": "NUMERIC",
            "mode": "REQUIRED",
        },
    ]
