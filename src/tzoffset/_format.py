"""Format a UTC offset as a bare numeric string."""

from __future__ import annotations

from datetime import datetime, timedelta, tzinfo

from ._checks import choice, kind
from ._errors import OffsetError
from ._types import STYLES, ZEROS, Style, Zero

_SECONDS_PER_DAY = 24 * 3600


def format_offset(
    value: timedelta | tzinfo | datetime, *, style: Style = "colon", zero: Zero = "+"
) -> str:
    """Format an offset as "+05:30", "+0530" or "+05".

    ``value`` is a ``timedelta``, a ``tzinfo`` with a fixed offset (such as
    ``datetime.timezone``), or an aware ``datetime``, which is the way to format a
    ``zoneinfo.ZoneInfo`` at a given moment. ``style`` is ``"colon"`` (``+05:30``),
    ``"compact"`` (``+0530``) or ``"short"`` (``+05`` when minutes and seconds are zero,
    otherwise the colon form); a seconds field is written only when the seconds are not
    zero. A zero offset is written with a plus sign, with a minus sign (``zero="-"``) or
    as ``Z`` (``zero="Z"``).

    Raises ``OffsetError`` (a ``ValueError``) for an offset of a day or more, a fraction of
    a second, a naive ``datetime``, a ``tzinfo`` without a fixed offset, or an unknown
    ``style`` or ``zero``; ``TypeError`` for a ``value`` of another type, a ``tzinfo``
    whose ``utcoffset(None)`` returns something other than a ``timedelta`` or ``None``,
    or a ``style`` or ``zero`` that is not a ``str``.

    >>> from datetime import timedelta, timezone
    >>> from tzoffset import format_offset
    >>> format_offset(timedelta(hours=5, minutes=30))
    '+05:30'
    >>> format_offset(timedelta(hours=-8), style="compact")
    '-0800'
    >>> format_offset(timezone(timedelta(hours=9)), style="short")
    '+09'
    >>> format_offset(timedelta(hours=-4, minutes=-56, seconds=-2))
    '-04:56:02'
    >>> format_offset(timezone.utc), format_offset(timezone.utc, zero="Z")
    ('+00:00', 'Z')
    """
    form = choice(style, "style", STYLES)
    zero_form = choice(zero, "zero", ZEROS)
    delta = _as_timedelta(value)
    if delta.microseconds:
        raise OffsetError(f"offset is not a whole number of seconds: {timedelta.__repr__(delta)}")
    total = delta.days * _SECONDS_PER_DAY + delta.seconds
    if abs(total) >= _SECONDS_PER_DAY:
        raise OffsetError(
            f"offset out of range: {timedelta.__repr__(delta)} (it must be under one day)"
        )
    if total == 0 and zero_form == "Z":
        return "Z"
    sign = "-" if total < 0 or (total == 0 and zero_form == "-") else "+"
    hours, remainder = divmod(abs(total), 3600)
    minutes, seconds = divmod(remainder, 60)
    if form == "short" and minutes == 0 and seconds == 0:
        return f"{sign}{hours:02d}"
    separator = "" if form == "compact" else ":"
    body = f"{hours:02d}{separator}{minutes:02d}"
    if seconds:
        body += f"{separator}{seconds:02d}"
    return f"{sign}{body}"


def _as_timedelta(value: object) -> timedelta:
    if isinstance(value, timedelta):
        return value
    if isinstance(value, datetime):
        # datetime itself checks that its tzinfo returns None or a timedelta under a day.
        offset = value.utcoffset()
        if offset is None:
            raise OffsetError(f"a naive datetime has no UTC offset: {datetime.isoformat(value)}")
        return offset
    if isinstance(value, tzinfo):
        fixed = value.utcoffset(None)
        if fixed is None:
            raise OffsetError(
                f"{kind(value)} has no fixed offset; pass an aware datetime to pick a moment"
            )
        if not isinstance(fixed, timedelta):
            raise TypeError(
                f"{kind(value)}.utcoffset(None) returned {kind(fixed)}, not a timedelta or None"
            )
        return fixed
    raise TypeError(f"expected a timedelta, tzinfo or datetime, not {kind(value)}")
