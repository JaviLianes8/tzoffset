"""Ground truth from the tz database source files (python scripts/fetch_vectors.py).

Every standard offset written in the Zone lines of tzdata 2026e, fetched from
https://data.iana.org/time-zones/releases/tzdata2026e.tar.gz (fetched 2026-10-18, checked
again 2026-10-27 against MANIFEST.txt), formats and parses back to the same offset.
"""

from __future__ import annotations

import io
import tarfile
from datetime import timedelta

from conftest import source_bytes

from tzoffset import Style, format_offset, parse_offset

TZDATA = "tzdata2026e.tar.gz"
TZ_FILES = "africa antarctica asia australasia europe northamerica southamerica etcetera backzone"
STYLES: list[Style] = ["colon", "compact", "short"]


def _seconds(field: str) -> int:
    sign = -1 if field.startswith("-") else 1
    parts = [int(part) for part in field.lstrip("-").split(":")]
    parts += [0] * (3 - len(parts))
    return sign * (parts[0] * 3600 + parts[1] * 60 + parts[2])


def _tz_offsets() -> dict[str, str]:
    """Every standard offset field in the Zone lines of the tz data, with one zone using it."""
    offsets: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(source_bytes(TZDATA))) as archive:
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
