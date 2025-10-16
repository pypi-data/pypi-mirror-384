# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Test the bigquery.types.Geography validator."""

from __future__ import annotations

import typing

import pytest
from ldr.modelling import bigquery
from ldr.modelling.bigquery.types import Geography, GeographyValidator  # noqa: TCH002
from shapely import wkb, wkt

STRING_POINT = "POINT (1 2)"


class _Model(bigquery.Model):
    point: typing.Annotated[Geography, GeographyValidator]


def test_geography_string_validation() -> None:
    """Ensure a string format point is parsed correctly."""
    assert _Model.model_validate({"point": STRING_POINT}).point == wkt.loads(
        STRING_POINT,
    )


def test_geography_bytes_validation() -> None:
    """Ensure a bytes format point is parsed correctly."""
    bytes_point = wkt.loads(STRING_POINT).wkb
    assert _Model.model_validate({"point": bytes_point}).point == wkb.loads(bytes_point)


def test_geography_from_instance_validation() -> None:
    """Ensure a `Geography` object is parsed correctly."""
    point: Geography = wkt.loads(STRING_POINT)
    assert _Model.model_validate({"point": point}).point == point


def test_geography_from_geojson_validation() -> None:
    """Ensure a `Geography` object is parsed from GeoJSON correctly."""
    point: dict[str, typing.Any] = {
        "type": "Point",
        "coordinates": [30.936, 19.121],
    }

    assert _Model.model_validate({"point": point}).point.wkt == "POINT (30.936 19.121)"


def test_geography_fails_to_parse_invalid_string() -> None:
    """Ensure the validator raises a ValueError when invalid input is provided."""
    with pytest.raises(ValueError, match="Invalid WKT string: .*"):
        _Model.model_validate({"point": "POINT (1,2)"})


def test_geography_fails_to_parse_invalid_bytes() -> None:
    """Ensure the validator raises a ValueError when invalid input is provided."""
    with pytest.raises(ValueError, match="Invalid WKB bytes: .*"):
        _Model.model_validate({"point": b"POINT (1,2)"})


def test_geography_fails_to_parse_invalid_geojson() -> None:
    """Ensure the validator raises a ValueError when invalid GeoJSON is provided."""
    with pytest.raises(ValueError, match="Invalid GeoJSON: .*"):
        _Model.model_validate({"point": {"type": "PIONT", "coordinates": [123, 101]}})


def test_geography_fails_to_parse_unsupported_type() -> None:
    """Ensure the validator raises a ValueError when invalid input is provided."""
    with pytest.raises(
        TypeError,
        match="Input must be a WKT string, WKB bytes, a GeoJSON format dict, "
        "or a Shapely geometry object",
    ):
        _Model.model_validate({"point": (1, 2)})


def test_geography_to_bq_schema() -> None:
    """Ensure the model field dumps as numeric."""
    assert _Model.to_bigquery_schema_dict() == [
        {
            "name": "point",
            "type": "GEOGRAPHY",
            "mode": "REQUIRED",
        },
    ]
