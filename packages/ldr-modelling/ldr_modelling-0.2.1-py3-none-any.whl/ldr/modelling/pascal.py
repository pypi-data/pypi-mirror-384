# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Base model for models with an alias generator for PascalCase."""

from __future__ import annotations

import pydantic
from pydantic.alias_generators import to_pascal


class Model(pydantic.BaseModel, alias_generator=to_pascal):
    """Default model config to alias field names to PascalCase."""
