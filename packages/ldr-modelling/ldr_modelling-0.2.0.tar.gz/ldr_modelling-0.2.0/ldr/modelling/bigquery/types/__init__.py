# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""
Additional custom datatypes to assist in serialising BigQuery types.

Annotate model fields using the following types:

TIMESTAMP - `ldr.modelling.bigquery.types.Timestamp`
GEOGRAPHY - `ldr.modelling.bigquery.types.Geography`
"""

from __future__ import annotations

__all__ = (
    "BigNumeric",
    "BigNumericValidator",
    "Geography",
    "GeographyValidator",
    "Numeric",
    "NumericValidator",
    "Timestamp",
    "TimestampValidator",
)

from ldr.modelling.bigquery.types.bignumeric import BigNumeric, BigNumericValidator
from ldr.modelling.bigquery.types.geography import Geography, GeographyValidator
from ldr.modelling.bigquery.types.numeric import Numeric, NumericValidator
from ldr.modelling.bigquery.types.timestamp import Timestamp, TimestampValidator
