"""Command line tool: normalise UTC offsets, or print the offset of a zone at a moment."""

from __future__ import annotations

import argparse
import errno
import os
import re
import sys
from collections.abc import Sequence
from datetime import datetime, timezone

from ._errors import OffsetError
from ._format import format_offset
from ._parse import parse_offset
from ._types import GRAMMARS, STYLES, ZEROS

_MARK = "\x00"


# A date and time with a trailing offset: the time part holds only digits, colons and a
# decimal mark, so the offset cannot be confused with the dashes of the date.
_AT = re.compile(r"(?P<local>.+[Tt ][0-9:.,]+?)(?P<offset>[Zz]|[+-][0-9:]+)")


def _shield_offsets(argv: Sequence[str]) -> list[str]:
    # argparse reads "-08:00" as an unknown option. Mark dash-led offsets before any "--"
    # so they stay positional, in order; _offset removes the mark again.
    cut = list(argv).index("--") if "--" in argv else len(argv)
    head = [_MARK + arg if re.match(r"-[0-9]", arg) else arg for arg in argv[:cut]]
    return [*head, *argv[cut:]]


def _offset(text: str) -> str:
    return text[len(_MARK) :] if text.startswith(_MARK) else text


def _parser() -> argparse.ArgumentParser:
    from . import __version__

    parser = argparse.ArgumentParser(
        prog="tzoffset",
        description="Rewrite UTC offsets in one style, one per line, or print the offset "
        "of a tz database zone at a moment.",
        epilog="examples:\n  tzoffset +0530 -08 Z\n"
        "  tzoffset --zone Europe/Madrid --at 2026-07-01T12:00",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "offsets", nargs="*", type=_offset, metavar="OFFSET", help="offsets to rewrite"
    )
    parser.add_argument("-s", "--style", choices=STYLES, default="colon", help="output style")
    parser.add_argument(
        "-z", "--zero", choices=ZEROS, default="+", help="how to write a zero offset (default +)"
    )
    parser.add_argument(
        "-g", "--grammar", choices=GRAMMARS, default="lenient", help="input grammar"
    )
    parser.add_argument("--zone", help="tz database name such as Europe/Madrid")
    parser.add_argument(
        "--at", help="ISO 8601 moment for --zone; a naive one is wall time there (default: now)"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _moment(text: str) -> datetime:
    # Before 3.11 fromisoformat reads neither "Z" nor "+0900", so the offset is split off and
    # read by this library; the rest is a plain local date and time.
    match = _AT.fullmatch(text)
    if match is None:
        return datetime.fromisoformat(text)
    local = datetime.fromisoformat(match["local"])
    return local.replace(tzinfo=parse_offset(match["offset"]))


def _zone_moment(parser: argparse.ArgumentParser, name: str, at: str | None) -> datetime:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

    try:
        zone = ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        # OSError: a folder of the database such as "America" is not a zone.
        if not available_timezones():
            parser.error("no time zone database found; install the tzdata package")
        parser.error(f"unknown time zone: {name!r}")
    if at is None:
        return datetime.now(timezone.utc).astimezone(zone)
    try:
        moment = _moment(at)
    except ValueError:
        parser.error(f"--at is not an ISO 8601 datetime: {at!r}")
    if moment.tzinfo is None:
        return moment.replace(tzinfo=zone)
    return moment.astimezone(zone)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``tzoffset`` and ``python -m tzoffset``; returns the exit code."""
    parser = _parser()
    args = parser.parse_intermixed_args(_shield_offsets(sys.argv[1:] if argv is None else argv))
    if args.zone is None and args.at is not None:
        parser.error("--at needs --zone")
    if (args.zone is None) == (not args.offsets):
        parser.error("give either OFFSET values or --zone")
    try:
        if args.zone is not None:
            moment = _zone_moment(parser, args.zone, args.at)
            lines = [format_offset(moment, style=args.style, zero=args.zero)]
        else:
            lines = [
                format_offset(
                    parse_offset(text, grammar=args.grammar), style=args.style, zero=args.zero
                )
                for text in args.offsets
            ]
    except OffsetError as error:
        parser.error(str(error))
    try:
        sys.stdout.write("".join(line + "\n" for line in lines))
        sys.stdout.flush()
    except OSError as error:
        # The reader went away (``| head``). Windows reports EINVAL rather than EPIPE.
        if not isinstance(error, BrokenPipeError) and error.errno != errno.EINVAL:
            raise
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
    return 0
