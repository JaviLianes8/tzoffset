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


def moment(text: str) -> datetime:
    """Read an --at value: what ``datetime.fromisoformat`` reads, with any offset read here."""
    # Before 3.11 fromisoformat reads neither "Z" nor "+0900", so the offset is split off and
    # read by this library; the rest is a plain local date and time.
    match = _AT.fullmatch(text)
    if match is None:
        return datetime.fromisoformat(text)
    local = datetime.fromisoformat(match["local"])
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
        parser.error(f"--at is not an ISO 8601 datetime: {quote(at)}")
    if when.tzinfo is None:
        return when.replace(tzinfo=zone)
    try:
        return when.astimezone(zone)
    except OverflowError:
        # The same instant falls before year 1 or after year 9999 on the zone's clock.
        parser.error(f"--at is out of range in {quote(name)}: {quote(at)}")
