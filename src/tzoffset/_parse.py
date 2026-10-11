"""Parse a bare numeric UTC offset into a timezone."""

from __future__ import annotations

import re
from datetime import timedelta, timezone

from ._errors import OffsetError

# Accepts +HH, +HHMM, +HH:MM, +HHMMSS and +HH:MM:SS. Colon and compact forms do
# not mix: once a colon appears the rest of the string must use colons too.
_PATTERN = re.compile(
    r"""
    (?P<sign>[+-])
    (?P<hh>\d{2})
    (?:
        :(?P<mm_colon>\d{2})(?::(?P<ss_colon>\d{2}))?
        |
        (?P<mm_compact>\d{2})(?P<ss_compact>\d{2})?
    )?
    """,
    re.VERBOSE,
)

_SECONDS_PER_DAY = 24 * 3600


def parse_offset(text: str) -> timezone:
    """Parse "Z", "+09", "+0530" or "+05:30" (optional seconds) into a timezone."""
    stripped = text.strip()
    if stripped in ("Z", "z"):
        return timezone.utc
    match = _PATTERN.fullmatch(stripped)
    if match is None:
        raise OffsetError(f"not a valid UTC offset: {text!r}")
    hours = int(match["hh"])
    minutes = int(match["mm_colon"] or match["mm_compact"] or 0)
    seconds = int(match["ss_colon"] or match["ss_compact"] or 0)
    if minutes > 59 or seconds > 59:
        raise OffsetError(f"offset field out of range: {text!r}")
    total = hours * 3600 + minutes * 60 + seconds
    if total >= _SECONDS_PER_DAY:
        raise OffsetError(f"offset out of range: {text!r}")
    if match["sign"] == "-":
        total = -total
    return timezone(timedelta(seconds=total))
