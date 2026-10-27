"""The error raised when an offset cannot be parsed or formatted."""

from __future__ import annotations


class OffsetError(ValueError):
    """Raised when a string is not a valid UTC offset, or a value is out of range.

    It is a ``ValueError``, so existing ``except ValueError`` handlers catch it. Arguments
    of the wrong type raise ``TypeError`` instead. A message quotes at most 40 characters
    of a text argument, followed by its length when it is longer; an offset is shown as
    its exact ``timedelta``, so every message stays short.

    >>> from tzoffset import OffsetError, parse_offset
    >>> try:
    ...     parse_offset("+25:00")
    ... except OffsetError as error:
    ...     print(error)
    offset field out of range: '+25:00' (hours 00-23, minutes and seconds 00-59)
    >>> isinstance(OffsetError("bad"), ValueError)
    True
    """
