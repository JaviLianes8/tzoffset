"""Parse a bare numeric UTC offset into a timezone."""

from __future__ import annotations

import re
from datetime import timedelta, timezone

from ._errors import OffsetError
from ._types import GRAMMARS, Grammar

_ASCII_SPACE = " \t\n\r\f\v"
# Digits are spelled [0-9]: \d would also take Arabic-Indic and other Unicode digits.
_SIGN_HOURS = r"(?P<sign>[+-])(?P<hh>[0-9]{2})"
_PATTERNS = {
    # 0.1 behaviour: +hh, +hhmm, +hh:mm, +hhmmss, +hh:mm:ss. Colon and compact never mix.
    "lenient": re.compile(
        _SIGN_HOURS + r"(?::(?P<mc>[0-9]{2})(?::(?P<sc>[0-9]{2}))?"
        r"|(?P<mp>[0-9]{2})(?P<sp>[0-9]{2})?)?"
    ),
    # RFC 3339 section 5.6: time-numoffset = ("+" / "-") time-hour ":" time-minute
    "rfc3339": re.compile(_SIGN_HOURS + r":(?P<mc>[0-9]{2})"),
    # RFC 3339 Appendix A (ISO 8601): ("+" / "-") time-hour [[":"] time-minute]
    "iso8601": re.compile(_SIGN_HOURS + r"(?::(?P<mc>[0-9]{2})|(?P<mp>[0-9]{2}))?"),
}


def _read(text: str, grammar: Grammar) -> tuple[int, bool]:
    """Return the offset in seconds and whether it marks an unknown local offset."""
    if not isinstance(text, str):
        raise TypeError(f"offset must be a str, not {type(text).__name__}")
    if grammar not in GRAMMARS:
        raise OffsetError(f"unknown grammar: {grammar!r}")
    # Only the lenient grammar forgives surrounding whitespace, and only ASCII whitespace:
    # protocol text is ASCII. The strict grammars are exact.
    body = text.strip(_ASCII_SPACE) if grammar == "lenient" else text
    if body in ("Z", "z"):
        return 0, True
    match = _PATTERNS[grammar].fullmatch(body)
    if match is None:
        raise OffsetError(f"not a valid {grammar} UTC offset: {text!r}")
    hours = int(match["hh"])
    minutes = int(match.groupdict().get("mc") or match.groupdict().get("mp") or 0)
    seconds = int(match.groupdict().get("sc") or match.groupdict().get("sp") or 0)
    # Hours stop at 23 so the magnitude stays under the one day Python allows.
    if hours > 23 or minutes > 59 or seconds > 59:
        raise OffsetError(f"offset field out of range: {text!r}")
    total = hours * 3600 + minutes * 60 + seconds
    if match["sign"] == "-":
        if total == 0 and grammar == "iso8601":
            raise OffsetError(f"ISO 8601 does not allow a negative zero offset: {text!r}")
        return -total, total == 0
    return total, False


def parse_offset(text: str, *, grammar: Grammar = "lenient") -> timezone:
    """Parse "Z", "+09", "+0530" or "+05:30" into a fixed-offset timezone.

    ``grammar="lenient"`` (the default) also takes seconds and surrounding ASCII spaces;
    ``"rfc3339"`` takes only ``Z`` and ``+hh:mm``; ``"iso8601"`` takes ``Z``, ``+hh``,
    ``+hhmm`` and ``+hh:mm`` but no negative zero. Raises ``OffsetError`` on bad text.
    """
    seconds, _ = _read(text, grammar)
    return timezone(timedelta(seconds=seconds))


def is_unknown_local_offset(text: str, *, grammar: Grammar = "lenient") -> bool:
    """Tell whether a valid offset says the local offset is unknown.

    True for ``Z`` and a negative zero such as ``-00:00`` (RFC 3339 section 4.3 as updated by
    RFC 9557 section 2); false for ``+00:00`` and every non-zero offset. Raises
    ``OffsetError`` when the text is not an offset in the grammar.
    """
    return _read(text, grammar)[1]
