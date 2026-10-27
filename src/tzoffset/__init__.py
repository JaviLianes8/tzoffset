"""Parse and format bare numeric UTC offsets (Z, +05:30, -0800) both ways.

>>> from tzoffset import format_offset, parse_offset
>>> format_offset(parse_offset("+0530"))
'+05:30'
>>> format_offset(parse_offset("-08:00"), style="compact")
'-0800'
"""

from ._errors import OffsetError
from ._format import format_offset
from ._parse import is_unknown_local_offset, parse_offset
from ._types import Grammar, Style, Zero

__version__ = "1.0.0"

# The error shows and pickles as tzoffset.OffsetError, never through its private module.
OffsetError.__module__ = __name__

__all__ = [
    "Grammar",
    "OffsetError",
    "Style",
    "Zero",
    "format_offset",
    "is_unknown_local_offset",
    "parse_offset",
]
