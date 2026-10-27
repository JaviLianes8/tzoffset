"""The --zone and --at side of the command line tool."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone

from ._checks import quote
from ._parse import parse_offset

# A date and time with a trailing offset: the time part holds only digits, colons and a
# decimal mark, so the offset cannot be confused with the dashes of the date.
_AT = re.compile(r"(?P<local>.+[Tt ][0-9:.,]+?)(?P<offset>[Zz]|[+-][0-9:]+)")
# The seconds of an extended time of day and their fraction, if any.
_SECONDS = re.compile(
    r"(?P<head>[Tt ][0-9]{2}:[0-9]{2}:)(?P<second>[0-9]{2})(?:[.,](?P<part>[0-9]+))?"
)


def _extended(text: str) -> str:
    """Spell the seconds of ``text`` so that ``datetime.fromisoformat`` of 3.10 reads them."""
    match = _SECONDS.search(text)
    if match is None:
        return text
    # A leap second (RFC 3339 allows second 60) is read as second 59 of the same minute: the
    # offset in force cannot change inside it. Before 3.11 fromisoformat reads only a
    # fraction of 3 or 6 digits after a dot; later ones keep 6 digits and cut the rest.
    second = "59" if match["second"] == "60" else match["second"]
    part = match["part"]
    fraction = "" if part is None else "." + (part + "00000")[:6]
    return text[: match.start()] + match["head"] + second + fraction + text[match.end() :]


def moment(text: str) -> datetime:
    """Read an --at value: what ``datetime.fromisoformat`` reads, with any offset read here."""
    # Before 3.11 fromisoformat reads neither "Z" nor "+0900", so the offset is split off and
    # read by this library; the rest is a plain local date and time.
    match = _AT.fullmatch(text)
    if match is None:
        return datetime.fromisoformat(_extended(text))
    local = datetime.fromisoformat(_extended(match["local"]))
    return local.replace(tzinfo=parse_offset(match["offset"]))


def zone_moment(parser: argparse.ArgumentParser, name: str, at: str | None) -> datetime:
    """Return the moment ``at`` (now when it is None) in the tz database zone ``name``."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

    try:
        zone = ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        # OSError: a folder of the database such as "America" is not a zone.
        if not available_timezones():
            parser.error("no time zone database found; install the tzdata package")
        parser.error(f"unknown time zone: {quote(name)}")
    if at is None:
        return datetime.now(timezone.utc).astimezone(zone)
    try:
        when = moment(at)
    except ValueError:
        parser.error(
            f"cannot read --at as a date and time: {quote(at)} "
            "(expected a form such as 2026-07-01T12:00:00+02:00)"
        )
    if when.tzinfo is None:
        return when.replace(tzinfo=zone)
    try:
        return when.astimezone(zone)
    except OverflowError:
        # The same instant falls before year 1 or after year 9999 on the zone's clock.
        parser.error(f"--at is out of range in {quote(name)}: {quote(at)}")
