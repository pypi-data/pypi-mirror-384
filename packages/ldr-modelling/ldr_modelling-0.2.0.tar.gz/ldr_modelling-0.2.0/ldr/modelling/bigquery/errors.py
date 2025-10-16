# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""BigQuery schema generation errors."""

from __future__ import annotations


class UnsupportedTypeError(ValueError):
    """An annotated type is not representable in BigQuery."""


class InvalidTypeError(TypeError):
    """A Literal annotation is invalid."""


class MissingAnnotationError(InvalidTypeError):
    """A field has no type annotation."""


class MissingAliasError(InvalidTypeError):
    """A field has no alias set."""
