"""Format a UTC offset as a bare numeric string."""

from __future__ import annotations

from datetime import datetime, timedelta, tzinfo

from ._errors import OffsetError
from ._types import STYLES, ZEROS, Style, Zero

_SECONDS_PER_DAY = 24 * 3600


def format_offset(
    value: timedelta | tzinfo | datetime, *, style: Style = "colon", zero: Zero = "+"
) -> str:
    """Format an offset as "+05:30", "+0530" or "+09".

    ``value`` is a ``timedelta``, a ``tzinfo`` with a fixed offset (``timezone``), or an aware
    ``datetime``, the way to format a ``zoneinfo.ZoneInfo`` at a given moment. A zero offset
    is written with a plus sign, with a minus sign (``zero="-"``) or as ``Z`` (``zero="Z"``).
    """
    if style not in STYLES:
        raise OffsetError(f"unknown style: {style!r}")
    if zero not in ZEROS:
        raise OffsetError(f"unknown zero spelling: {zero!r}")
    delta = _as_timedelta(value)
    if delta.microseconds:
        raise OffsetError(f"offset is not a whole number of seconds: {delta!r}")
    total = delta.days * _SECONDS_PER_DAY + delta.seconds
    if abs(total) >= _SECONDS_PER_DAY:
        raise OffsetError(f"offset out of range: {delta!r}")
    if total == 0 and zero == "Z":
        return "Z"
    sign = "-" if total < 0 or (total == 0 and zero == "-") else "+"
    hours, remainder = divmod(abs(total), 3600)
    minutes, seconds = divmod(remainder, 60)
    if style == "short" and minutes == 0 and seconds == 0:
        return f"{sign}{hours:02d}"
    separator = "" if style == "compact" else ":"
    body = f"{hours:02d}{separator}{minutes:02d}"
    if seconds:
        body += f"{separator}{seconds:02d}"
    return f"{sign}{body}"


def _as_timedelta(value: timedelta | tzinfo | datetime) -> timedelta:
    if isinstance(value, timedelta):
        return value
    if isinstance(value, datetime):
        offset = value.utcoffset()
        if offset is None:
            raise OffsetError(f"naive datetime has no UTC offset: {value!r}")
        return offset
    if isinstance(value, tzinfo):
        offset = value.utcoffset(None)
        if offset is None:
            raise OffsetError(
                f"{value!r} has no fixed offset; pass an aware datetime to pick a moment"
            )
        return offset
    raise TypeError(f"expected a timedelta, tzinfo or datetime, not {type(value).__name__}")
