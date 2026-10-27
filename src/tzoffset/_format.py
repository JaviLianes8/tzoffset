"""Format a UTC offset as a bare numeric string."""

from __future__ import annotations

from datetime import date, datetime, timedelta, tzinfo
from typing import TypeGuard, TypeVar

from ._checks import choice, kind
from ._errors import OffsetError
from ._types import STYLES, ZEROS, Style, Zero

_SECONDS_PER_DAY = 24 * 3600
_T = TypeVar("_T")
# The C-level tzinfo field of a datetime, which a subclass cannot override.
_DATETIME_TZINFO = vars(datetime)["tzinfo"]
# The C-level date and time fields of a datetime, for a message that asks nobody else.
_FIELDS = tuple(vars(date)[name] for name in ("year", "month", "day")) + tuple(
    vars(datetime)[name] for name in ("hour", "minute", "second", "microsecond")
)


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
    (also the one of a ``datetime``) whose ``utcoffset`` returns something other than a
    ``timedelta`` or ``None``, or a ``style`` or ``zero`` that is not a ``str``. A subclass
    of ``timedelta`` or ``datetime`` is read by its stored value, never by its own methods;
    an object that only claims to be one (a mock with ``spec=timedelta``) is a ``TypeError``.

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
    # Every offset is copied into an exact timedelta first: a subclass may override days,
    # seconds or __repr__, and only the stored value may count.
    if _is(value, timedelta):
        return _exact(value)
    if _is(value, datetime):
        # The tzinfo is read from the datetime itself and range-checked here, so a subclass
        # cannot change the offset and an offset of a day or more is an OffsetError.
        zone = _DATETIME_TZINFO.__get__(value, datetime)
        offset = None if zone is None else _offset(zone, value)
        if offset is None:
            raise OffsetError(f"a naive datetime has no UTC offset: {_naive_text(value)}")
        return offset
    if isinstance(value, tzinfo):
        fixed = _offset(value, None)
        if fixed is None:
            raise OffsetError(
                f"{kind(value)} has no fixed offset; pass an aware datetime to pick a moment"
            )
        return fixed
    raise TypeError(f"expected a timedelta, tzinfo or datetime, not {kind(value)}")


def _offset(zone: tzinfo, moment: datetime | None) -> timedelta | None:
    """Return ``zone.utcoffset(moment)`` as an exact timedelta, or None."""
    offset: object = zone.utcoffset(moment)
    if offset is None:
        return None
    if not _is(offset, timedelta):
        at = "None" if moment is None else "a datetime"
        raise TypeError(
            f"{kind(zone)}.utcoffset({at}) returned {kind(offset)}, not a timedelta or None"
        )
    return _exact(offset)


def _exact(delta: timedelta) -> timedelta:
    # timedelta.__add__ reads the stored fields and returns a plain timedelta.
    return timedelta.__add__(timedelta(0), delta)


def _is(value: object, cls: type[_T]) -> TypeGuard[_T]:
    # Only the real type counts: Mock(spec=timedelta) passes isinstance through a spoofed
    # __class__ without holding the stored fields this module reads.
    return issubclass(type(value), cls)


def _naive_text(value: datetime) -> str:
    # The tzinfo is not asked again: it may answer differently the second time.
    return datetime(*(field.__get__(value) for field in _FIELDS)).isoformat()
