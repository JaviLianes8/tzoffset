"""Parse and format bare numeric UTC offsets (Z, +05:30, -0800) both ways."""

from __future__ import annotations

from ._errors import OffsetError
from ._format import format_offset
from ._parse import parse_offset

__version__ = "0.1.0"

__all__ = ["OffsetError", "format_offset", "parse_offset"]
