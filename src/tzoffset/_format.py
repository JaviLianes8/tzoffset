"""Format a UTC offset as a bare numeric string."""

from __future__ import annotations

from datetime import timedelta, timezone

from ._errors import OffsetError

_SECONDS_PER_DAY = 24 * 3600
_STYLES = ("colon", "compact", "short")


def format_offset(value: timezone | timedelta, *, style: str = "colon") -> str:
    """Format a timezone or timedelta as "+05:30", "+0530" or "+09"."""
    if style not in _STYLES:
        raise OffsetError(f"unknown style: {style!r}")
    delta = _as_timedelta(value)
    if delta.microseconds:
        raise OffsetError(f"offset is not a whole number of seconds: {delta!r}")
    total = delta.days * _SECONDS_PER_DAY + delta.seconds
    if abs(total) >= _SECONDS_PER_DAY:
        raise OffsetError(f"offset out of range: {delta!r}")
    sign = "-" if total < 0 else "+"
    hours, remainder = divmod(abs(total), 3600)
    minutes, seconds = divmod(remainder, 60)
    if style == "short" and minutes == 0 and seconds == 0:
        return f"{sign}{hours:02d}"
    separator = "" if style == "compact" else ":"
    body = f"{hours:02d}{separator}{minutes:02d}"
    if seconds:
        body += f"{separator}{seconds:02d}"
    return f"{sign}{body}"


def _as_timedelta(value: timezone | timedelta) -> timedelta:
    if isinstance(value, timedelta):
        return value
    offset = value.utcoffset(None)
    if offset is None:
        raise OffsetError(f"timezone has no fixed offset: {value!r}")
    return offset
