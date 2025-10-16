# Copyright 2025 Louder Digital Pty Ltd.
# All Rights Reserved.
"""Base model for models with an alias generator for snake_case."""
from __future__ import annotations

import pydantic
from pydantic.alias_generators import to_snake


class Model(pydantic.BaseModel, alias_generator=to_snake):
    """Default model config to alias field names to snake_case."""
