"""The error raised when an offset cannot be parsed or formatted."""

from __future__ import annotations


class OffsetError(ValueError):
    """Raised when a string is not a valid UTC offset, or a value is out of range."""
