"""Ground truth from the fetched sources (python scripts/fetch_vectors.py).

The RFC grammar lines and the tz database offsets are read from the files listed in
tests/vectors/sources/MANIFEST.txt; the tests skip when the folder has not been fetched.
"""

from __future__ import annotations

import re
import tarfile
from datetime import timedelta
from pathlib import Path

import pytest

from tzoffset import (
    Grammar,
    OffsetError,
    Style,
    format_offset,
    is_unknown_local_offset,
    parse_offset,
)

SOURCES = Path(__file__).resolve().parent / "vectors" / "sources"
TZDATA = "tzdata2026e.tar.gz"
# The tz database, https://data.iana.org/time-zones/releases/tzdata2026e.tar.gz
TZ_FILES = "africa antarctica asia australasia europe northamerica southamerica etcetera backzone"
STYLES: list[Style] = ["colon", "compact", "short"]


def _squashed(name: str) -> str:
    path = SOURCES / name
    if not path.is_file():
        pytest.skip(f"{name} not fetched; run python scripts/fetch_vectors.py")
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def _accepted(grammar: Grammar, candidates: list[str]) -> set[str]:
    accepted = set()
    for text in candidates:
        try:
            parse_offset(text, grammar=grammar)
        except OffsetError:
            continue
        accepted.add(text)
    return accepted


# Every sign, hour 00-25 and minute 00-61, with and without a colon: wider than both grammars.
CANDIDATES = ["Z", "z"] + [
    f"{sign}{hour:02d}{tail}"
    for sign in "+-"
    for hour in range(26)
    for tail in ["", *(f"{sep}{minute:02d}" for sep in ("", ":") for minute in range(62))]
]


# Phrases below are cited from https://www.rfc-editor.org/rfc/rfc3339.txt (fetched 2026-10-13).
def test_rfc3339_offset_grammar_is_the_one_implemented() -> None:
    text = _squashed("rfc3339.txt")
    # Section 5.6, the profile the rfc3339 grammar follows.
    assert "time-hour = 2DIGIT ; 00-23 time-minute = 2DIGIT ; 00-59" in text
    assert 'time-numoffset = ("+" / "-") time-hour ":" time-minute' in text
    assert 'time-offset = "Z" / time-numoffset' in text
    assert 'the "T" and "Z" characters in this syntax may alternatively be lower case' in text
    # Appendix A, the ISO 8601 collection the iso8601 grammar follows.
    assert 'time-numoffset = ("+" / "-") time-hour [[":"] time-minute]' in text
    assert "time-hour = 2DIGIT ; 00-24" in text
    # Section 4.3: -00:00 for an unknown local offset.
    assert 'is unknown, this can be represented with an offset of "-00:00"' in text
    # The same rules written out by hand, then checked against the parser.
    rfc = {f"{s}{h:02d}:{m:02d}" for s in "+-" for h in range(24) for m in range(60)}
    assert _accepted("rfc3339", CANDIDATES) == rfc | {"Z", "z"}
    # Appendix A with hour 24 left out (no Python offset reaches a day) and, per RFC 9557,
    # no negative zero.
    iso = {f"{s}{h:02d}" for s in "+-" for h in range(24)}
    iso |= {f"{o}{sep}{m:02d}" for o in set(iso) for sep in ("", ":") for m in range(60)}
    iso -= {"-00", "-0000", "-00:00"}
    assert _accepted("iso8601", CANDIDATES) == iso | {"Z", "z"}


# Phrases below are cited from https://www.rfc-editor.org/rfc/rfc9557.txt (fetched 2026-10-13).
def test_rfc9557_reads_z_like_negative_zero() -> None:
    text = _squashed("rfc9557.txt")
    assert "interpreting the offset Z to mean the same as -00:00" in text
    assert "[ISO8601:2000] and later do not allow -00:00" in text
    assert is_unknown_local_offset("Z")
    assert is_unknown_local_offset("-00:00")
    assert not is_unknown_local_offset("+00:00")
    with pytest.raises(OffsetError):
        parse_offset("-00:00", grammar="iso8601")


def _seconds(field: str) -> int:
    sign = -1 if field.startswith("-") else 1
    parts = [int(part) for part in field.lstrip("-").split(":")]
    parts += [0] * (3 - len(parts))
    return sign * (parts[0] * 3600 + parts[1] * 60 + parts[2])


def _tz_offsets() -> dict[str, str]:
    """Every standard offset field in the Zone lines of the tz data, with one zone using it."""
    path = SOURCES / TZDATA
    if not path.is_file():
        pytest.skip(f"{TZDATA} not fetched; run python scripts/fetch_vectors.py")
    offsets: dict[str, str] = {}
    with tarfile.open(path) as archive:
        for member in TZ_FILES.split():
            handle = archive.extractfile(member)
            assert handle is not None
            zone, continues = "", False
            for raw in handle.read().decode("utf-8").splitlines():
                fields = raw.split("#")[0].split()
                if not fields:
                    continue  # blank and comment lines may sit inside a Zone block
                if fields[0] == "Zone":
                    zone, fields = fields[1], fields[2:]
                elif not continues:
                    continue
                offsets.setdefault(fields[0], zone)
                # STDOFF RULES FORMAT [UNTIL]: an UNTIL field means a continuation line follows.
                continues = len(fields) > 3
    return offsets


def test_every_tz_database_offset_round_trips() -> None:
    offsets = _tz_offsets()
    assert len(offsets) == 538
    assert "0:29:46" in offsets
    assert not [field for field in offsets if "." in field]
    for field, zone in offsets.items():
        delta = timedelta(seconds=_seconds(field))
        for style in STYLES:
            text = format_offset(delta, style=style)
            assert parse_offset(text).utcoffset(None) == delta, (field, zone)
        if delta.seconds % 60 == 0:
            assert parse_offset(format_offset(delta), grammar="rfc3339").utcoffset(None) == delta


def test_tz_database_extremes_are_the_documented_ones() -> None:
    offsets = _tz_offsets()
    ordered = sorted(offsets, key=_seconds)
    assert (ordered[0], offsets[ordered[0]]) == ("-15:56:08", "Asia/Manila")
    assert (ordered[-1], offsets[ordered[-1]]) == ("15:13:42", "America/Metlakatla")
    assert format_offset(timedelta(seconds=_seconds(ordered[0]))) == "-15:56:08"
    assert sum(1 for field in offsets if field.count(":") == 2) > 400
    assert {"14", "-12"} <= set(offsets)
