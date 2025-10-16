# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""
BigQuery `NUMERIC` wrapper on `decimal.Decimal`.

The `google-cloud-bigquery` library returns `NUMERIC` columns as
`decimal.Decimal` objects by default. This `Numeric` class is a type wrapper over
`decimal.Decimal` to indicate that your field in BigQuery should be `NUMERIC`
and not a `FLOAT` or `BIGNUMERIC`. It provides no other functionality.
"""

from __future__ import annotations

import decimal
import typing

if typing.TYPE_CHECKING:
    import pydantic_core


class Numeric(decimal.Decimal):
    """
    A marker type to indicate a field is `NUMERIC` to the BigQuery schema generator.

    Pydantic will validate this as a `decimal.Decimal` object, and serialise it as
    such. This works if using the `google-cloud-bigquery` client library, as `NUMERIC`
    columns are always returned as `decimal.Decimal` objects.
    """


class NumericValidator:
    """
    Pydantic validator for `Numeric` objects.

    This allows Pydantic to interpret `Numeric`s as  `decimal.Decimal`s, enabling
    compatibility with the `google-cloud-bigquery` client library while still generating
    the schema field type as `DECIMAL`.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: typing.Any,
        handler: typing.Any,
    ) -> pydantic_core.core_schema.CoreSchema:
        """
        Handle the pydantic schema hook for a `Timestamp` object.

        Returns
        -------
        The schema for a `datetime.datetime`. Includes parsing from ISO strings, etc.

        """
        # Tell Pydantic to use the validation schema for a decimal.Decimal.
        return handler(decimal.Decimal)
