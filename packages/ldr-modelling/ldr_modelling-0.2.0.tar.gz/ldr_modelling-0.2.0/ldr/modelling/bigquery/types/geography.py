# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""
BigQuery `GEOGRAPHY` wrapper on `shapely.geometry.base.BaseGeometry`.

The `google-cloud-bigquery` library returns `GEOMETRY` columns as
`BaseGeometry` objects by default. This `Geography` class is a type alias for
`BaseGeometry` to indicate that your field type in BigQuery should be `GEOGRAPHY`.

This also includes a pydantic validator for Geography objects.
"""

import typing

from pydantic_core import core_schema
from shapely import wkb, wkt
from shapely.errors import GEOSException
from shapely.geometry import base, shape

Geography = base.BaseGeometry


class GeographyValidator:
    """
    Handle the validation of `ldr.bigquery.types.Geography` objects.

    These `Geography` objects are simply an alias for
    `shapely.geometry.base.BaseGeometry` for convenience when working
    with this library.

    Handles parsing WKB, WKT, or existing `BaseGeometry` subclass.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: typing.Any,
        _handler: typing.Callable,
    ) -> core_schema.CoreSchema:
        """
        Handle the pydantic schema hook for a `Geography` object.

        Returns
        -------
        The schema for a `datetime.datetime`. Includes parsing from ISO strings, etc.

        """

        def validate(value: typing.Any) -> base.BaseGeometry:
            if isinstance(value, base.BaseGeometry):
                return value
            if isinstance(value, str):
                try:
                    return wkt.loads(value)
                except GEOSException as e:
                    raise ValueError(f"Invalid WKT string: {e}") from e
            elif isinstance(value, bytes):
                try:
                    return wkb.loads(value)
                except GEOSException as e:
                    raise ValueError(f"Invalid WKB bytes: {e}") from e
            elif isinstance(value, dict):
                try:
                    return shape(value)
                except Exception as e:  # noqa: BLE001
                    raise ValueError(f"Invalid GeoJSON: {e}") from e

            raise TypeError(
                "Input must be a WKT string, WKB bytes, a GeoJSON format dict, "
                "or a Shapely geometry object",
            )

        return core_schema.no_info_plain_validator_function(validate)
