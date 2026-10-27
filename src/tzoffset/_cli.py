"""Command line tool: normalise UTC offsets, or print the offset of a zone at a moment."""

from __future__ import annotations

import argparse
import errno
import os
import re
import sys
from collections.abc import Sequence
from typing import NoReturn

from ._cli_zone import zone_moment
from ._errors import OffsetError
from ._format import format_offset
from ._parse import parse_offset
from ._types import GRAMMARS, STYLES, ZEROS

_MARK = "\x00"
# argparse quotes a rejected argument whole; a longer message is cut to this many characters.
_MESSAGE_LIMIT = 200


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        if len(message) > _MESSAGE_LIMIT:
            message = message[: _MESSAGE_LIMIT - 3] + "..."
        super().error(message)


def _shield_offsets(argv: Sequence[str]) -> list[str]:
    # argparse reads "-08:00" as an unknown option. Mark dash-led arguments before any "--"
    # so they stay values, in order; _unshield removes the mark again.
    cut = list(argv).index("--") if "--" in argv else len(argv)
    head = [_MARK + arg if re.match(r"-[0-9]", arg) else arg for arg in argv[:cut]]
    return [*head, *argv[cut:]]


def _unshield(text: str) -> str:
    return text[len(_MARK) :] if text.startswith(_MARK) else text


def _parser() -> argparse.ArgumentParser:
    from . import __version__

    parser = _Parser(
        prog="tzoffset",
        description="Rewrite UTC offsets in one style, one per line, or print the offset "
        "of a tz database zone at a moment.",
        epilog="examples:\n  tzoffset +0530 -08 Z\n"
        "  tzoffset --zone Europe/Madrid --at 2026-07-01T12:00\n\n"
        "exit status: 0 done, 1 output closed early, 2 bad input",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "offsets", nargs="*", type=_unshield, metavar="OFFSET", help="offsets to rewrite"
    )
    parser.add_argument("-s", "--style", choices=STYLES, default="colon", help="output style")
    parser.add_argument(
        "-z", "--zero", choices=ZEROS, default="+", help="how to write a zero offset (default +)"
    )
    parser.add_argument(
        "-g", "--grammar", choices=GRAMMARS, default="lenient", help="input grammar"
    )
    parser.add_argument("--zone", type=_unshield, help="tz database name such as Europe/Madrid")
    parser.add_argument(
        "--at",
        type=_unshield,
        help="ISO 8601 moment for --zone; a naive one is wall time there (default: now)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _lines(parser: argparse.ArgumentParser, argv: Sequence[str]) -> list[str]:
    args = parser.parse_intermixed_args(_shield_offsets(argv))
    if args.zone is None and args.at is not None:
        parser.error("--at needs --zone")
    if (args.zone is None) == (not args.offsets):
        parser.error("give either OFFSET values or --zone")
    try:
        if args.zone is not None:
            moment = zone_moment(parser, args.zone, args.at)
            return [format_offset(moment, style=args.style, zero=args.zero)]
        return [
            format_offset(
                parse_offset(text, grammar=args.grammar), style=args.style, zero=args.zero
            )
            for text in args.offsets
        ]
    except OffsetError as error:
        parser.error(str(error))


def _deliver(text: str) -> bool:
    """Write ``text`` to standard output and flush it; False when the reader has gone away."""
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except OSError as error:
        # The reader went away (``| head``). Windows reports EINVAL rather than EPIPE.
        if not isinstance(error, BrokenPipeError) and error.errno != errno.EINVAL:
            raise
        # Python flushes standard output again at exit; point it at devnull so that is quiet.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
        return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for ``tzoffset`` and ``python -m tzoffset``; returns the exit status.

    0 when everything was written, 1 when the reader closed the output first; bad input
    and usage errors leave through argparse with ``SystemExit(2)``.
    """
    parser = _parser()
    try:
        lines = _lines(parser, sys.argv[1:] if argv is None else argv)
    except SystemExit as stop:
        # --help and --version print through argparse, which ignores write errors, so their
        # text may still wait in the buffer of a closed pipe.
        if not _deliver("") and stop.code == 0:
            raise SystemExit(1) from None
        raise
    return 0 if _deliver("".join(line + "\n" for line in lines)) else 1
