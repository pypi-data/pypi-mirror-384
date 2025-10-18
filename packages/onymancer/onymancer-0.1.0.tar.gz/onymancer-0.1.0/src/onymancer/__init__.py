"""Procedural fantasy name generation library."""

from .namegen import (
    generate,
    load_tokens_from_json,
    set_token,
    set_tokens,
)

__all__ = [
    "generate",
    "load_tokens_from_json",
    "set_token",
    "set_tokens",
]
