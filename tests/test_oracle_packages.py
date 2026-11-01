"""Two independent parsers from PyPI as oracles: rfc3339-validator and python-dateutil.

Both are test dependencies only (pip install -e .[dev]); the tests skip without them.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from tzoffset import Grammar, OffsetError, parse_offset

# Every sign, hour 00-25 and minute 00-61 with and without a colon, and boundary seconds.
CANDIDATES = ["Z", "z"] + [
    f"{sign}{hour:02d}{tail}"
    for sign in "+-"
    for hour in range(26)
    for tail in [
        "",
        *(f"{sep}{minute:02d}" for sep in ("", ":") for minute in range(62)),
        *(f"{sep}30{sep}{second:02d}" for sep in ("", ":") for second in (0, 59, 60)),
    ]
]


def _accepted(grammar: Grammar) -> dict[str, timedelta]:
    accepted = {}
    for text in CANDIDATES:
        try:
            offset = parse_offset(text, grammar=grammar).utcoffset(None)
        except OffsetError:
            continue
        assert offset is not None
        accepted[text] = offset
    return accepted


def test_rfc3339_grammar_matches_rfc3339_validator() -> None:
    validator = pytest.importorskip("rfc3339_validator")
    theirs = {
        text for text in CANDIDATES if validator.validate_rfc3339("2026-01-01T00:00:00" + text)
    }
    # The validator is case sensitive; RFC 3339 section 5.6 allows a lower-case "z".
    assert set(_accepted("rfc3339")) == theirs | {"z"}
    assert len(theirs) == 2 * 24 * 60 + 1


def test_iso8601_grammar_matches_dateutil_isoparser() -> None:
    parser_module = pytest.importorskip("dateutil.parser")
    parser = parser_module.isoparser()
    theirs = {}
    for text in CANDIDATES:
        try:
            zone = parser.parse_tzstr(text)
        except ValueError:
            continue
        theirs[text] = zone.utcoffset(None)
    mine = _accepted("iso8601")
    # dateutil reads the negative zero that RFC 9557 section 2 says ISO 8601 forbids.
    assert set(theirs) - set(mine) == {"-00", "-0000", "-00:00"}
    assert set(mine) <= set(theirs)
    assert all(theirs[text] == offset for text, offset in mine.items())
    assert len(mine) > 5000
