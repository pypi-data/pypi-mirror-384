# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""
BigQuery `TIMESTAMP` wrapper on `datetime.datetime`.

The `google-cloud-bigquery` library returns `TIMESTAMP` columns as
`datetime.datetime` objects by default, always in UTC. This `Timestamp`
class is a type wrapper over `datetime.datetime` to indicate that your
field in BigQuery should be a `TIMESTAMP` and not a `DATETIME`. It provides
no other functionality.
"""

from __future__ import annotations

import datetime
import typing

if typing.TYPE_CHECKING:
    import pydantic_core


class Timestamp(datetime.datetime):
    """
    A marker type to indicate a field is a `TIMESTAMP` to the BigQuery schema generator.

    Pydantic will validate this as a `datetime.datetime` object, and serialise it as
    such. This works if using the `google-cloud-bigquery` client library, as `TIMESTAMP`
    columns are always returned as `datetime.datetime` objects in UTC.
    """


class TimestampValidator:
    """
    Pydantic validator for `Timestamp` objects.

    This allows Pydantic to interpret `Timestamp`s as  `datetime.datetime`s, enabling
    compatibility with the `google-cloud-bigquery` client library while still generating
    the schema field type as `TIMESTAMP`.
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
        # Tell Pydantic to use the validation schema for a stdlib datetime.
        return handler(datetime.datetime)
