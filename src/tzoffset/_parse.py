"""Parse a bare numeric UTC offset into a timezone."""

from __future__ import annotations

import re
from datetime import timedelta, timezone

from ._checks import choice, plain, quote
from ._errors import OffsetError
from ._types import GRAMMARS, Grammar

_ASCII_SPACE = " \t\n\r\f\v"
# Digits are spelled [0-9]: \d would also take Arabic-Indic and other Unicode digits.
_SIGN_HOURS = r"(?P<sign>[+-])(?P<hh>[0-9]{2})"
_PATTERNS = {
    # +hh, +hhmm, +hh:mm, +hhmmss, +hh:mm:ss. Colon and compact never mix.
    "lenient": re.compile(
        _SIGN_HOURS + r"(?::(?P<mc>[0-9]{2})(?::(?P<sc>[0-9]{2}))?"
        r"|(?P<mp>[0-9]{2})(?P<sp>[0-9]{2})?)?"
    ),
    # RFC 3339 section 5.6: time-numoffset = ("+" / "-") time-hour ":" time-minute
    "rfc3339": re.compile(_SIGN_HOURS + r":(?P<mc>[0-9]{2})"),
    # RFC 3339 Appendix A (ISO 8601): ("+" / "-") time-hour [[":"] time-minute]
    "iso8601": re.compile(_SIGN_HOURS + r"(?::(?P<mc>[0-9]{2})|(?P<mp>[0-9]{2}))?"),
}


def _read(text: object, grammar: object) -> tuple[int, bool]:
    """Return the offset in seconds and whether it marks an unknown local offset."""
    original = plain(text, "offset")
    rule = choice(grammar, "grammar", GRAMMARS)
    # Only the lenient grammar forgives surrounding whitespace, and only ASCII whitespace:
    # protocol text is ASCII. The strict grammars are exact.
    body = original.strip(_ASCII_SPACE) if rule == "lenient" else original
    if body in ("Z", "z"):
        return 0, True
    match = _PATTERNS[rule].fullmatch(body)
    if match is None:
        raise OffsetError(f"not a valid {rule} UTC offset: {quote(original)}")
    fields = match.groupdict()
    hours = int(fields["hh"])
    minutes = int(fields.get("mc") or fields.get("mp") or 0)
    seconds = int(fields.get("sc") or fields.get("sp") or 0)
    # Hours stop at 23 so the magnitude stays under the one day Python allows.
    if hours > 23 or minutes > 59 or seconds > 59:
        raise OffsetError(
            f"offset field out of range: {quote(original)} (hours 00-23, minutes and seconds 00-59)"
        )
    total = hours * 3600 + minutes * 60 + seconds
    if fields["sign"] == "-":
        if total == 0 and rule == "iso8601":
            raise OffsetError(f"ISO 8601 does not allow a negative zero offset: {quote(original)}")
        return -total, total == 0
    return total, False


def parse_offset(text: str, *, grammar: Grammar = "lenient") -> timezone:
    """Parse "Z", "+09", "+0530" or "+05:30" into a fixed-offset ``datetime.timezone``.

    ``grammar="lenient"`` (the default) also takes a seconds field and surrounding ASCII
    whitespace; ``"rfc3339"`` takes only ``Z`` and ``+hh:mm``; ``"iso8601"`` takes ``Z``,
    ``+hh``, ``+hhmm`` and ``+hh:mm`` but no negative zero. ``Z`` may be lower case. Digits
    are ASCII, hours 00-23, minutes and seconds 00-59. A zero offset gives
    ``datetime.timezone.utc`` itself.

    Raises ``OffsetError`` (a ``ValueError``) for text that is not an offset in the grammar
    or an unknown grammar, and ``TypeError`` when ``text`` or ``grammar`` is not a ``str``.

    >>> from tzoffset import parse_offset
    >>> parse_offset("+05:30")
    datetime.timezone(datetime.timedelta(seconds=19800))
    >>> parse_offset("-0800").utcoffset(None)
    datetime.timedelta(days=-1, seconds=57600)
    >>> parse_offset("Z")
    datetime.timezone.utc
    >>> parse_offset("+0530", grammar="rfc3339")
    Traceback (most recent call last):
        ...
    tzoffset.OffsetError: not a valid rfc3339 UTC offset: '+0530'
    """
    seconds, _ = _read(text, grammar)
    return timezone(timedelta(seconds=seconds))


def is_unknown_local_offset(text: str, *, grammar: Grammar = "lenient") -> bool:
    """Tell whether a valid offset says that the local offset is unknown.

    True for ``Z`` and a negative zero such as ``-00:00`` or ``-0000`` (RFC 3339 section 4.3
    as updated by RFC 9557 section 2, and the ``-0000`` of RFC 5322 section 3.3); false for
    ``+00:00`` and every offset that is not zero. The text is validated first, with the
    same errors as ``parse_offset``.

    >>> from tzoffset import is_unknown_local_offset
    >>> is_unknown_local_offset("-00:00"), is_unknown_local_offset("Z")
    (True, True)
    >>> is_unknown_local_offset("+00:00"), is_unknown_local_offset("-05:00")
    (False, False)
    """
    return _read(text, grammar)[1]
