"""java.time.ZoneOffset as an independent oracle, from its recorded output.

tests/vectors/java/zoneoffset.txt is the output of scripts/oracle/ZoneOffsetOracle.java run
with OpenJDK 21.0.8 on 2026-10-27 (python scripts/java_oracle.py regenerates it). Java and
this library are compared input by input; the only differences allowed are the four listed
in _expected_difference, each a documented choice of one side.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from tzoffset import OffsetError, format_offset, parse_offset

VECTORS = Path(__file__).resolve().parent / "vectors" / "java" / "zoneoffset.txt"
JAVA_LIMIT = 18 * 3600  # ZoneOffset stops at +-18:00; Python, and this library, at a day


def _records(kind: str) -> list[tuple[str, str]]:
    records = []
    for line in VECTORS.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{kind} "):
            given, result = line[2:].split("\t")
            records.append((given, result))
    return records


def test_the_recorded_output_is_real_java_output() -> None:
    header = [line for line in VECTORS.read_text(encoding="utf-8").splitlines() if line[:1] == "#"]
    assert any(line.startswith("# openjdk version") for line in header)
    assert len(_records("P")) > 1900 and len(_records("F")) > 3000


def _mine(text: str) -> int | None:
    try:
        offset = parse_offset(text).utcoffset(None)
    except OffsetError:
        return None
    assert offset is not None
    return int(offset.total_seconds())


def _expected_difference(text: str, mine: int | None, java: int | None) -> bool:
    if java is not None and mine is None:
        # Java also reads a one-digit hour such as "+5"; offsets here always have two.
        return len(text) == 2
    if mine is not None and java is None:
        # Lower-case "z" (RFC 3339 section 5.6 allows it), surrounding ASCII whitespace
        # (lenient grammar), and magnitudes past Java's 18 hours.
        return text == "z" or text != text.strip() or abs(mine) > JAVA_LIMIT
    return False


def test_parse_agrees_with_zone_offset_of() -> None:
    differences = []
    for text, result in _records("P"):
        java = None if result == "ERR" else int(result)
        mine = _mine(text)
        if mine != java:
            assert _expected_difference(text, mine, java), (text, mine, java)
            differences.append(text)
    assert len(differences) > 100
    assert {"z", "+5", " +05:30", "+23:59:59"} <= set(differences)
    assert _mine("+18:00") == 64800 and _mine("+18:00:01") == 64801


def test_whatever_both_accept_has_the_same_value() -> None:
    agreed = [text for text, result in _records("P") if result != "ERR" and _mine(text) is not None]
    assert len(agreed) > 1000
    assert {"Z", "+05:30", "-0800", "-00:00", "+18:00:00", "-1759"} <= set(agreed)


@pytest.mark.parametrize("index", range(4))
def test_format_matches_the_java_spellings(index: int) -> None:
    # The id writes zero as Z; the patterns xxxxx, xxxx and the +HH:mm:ss builder write the
    # same colon, compact and short forms as this library.
    for given, result in _records("F"):
        delta = timedelta(seconds=int(given))
        mine = [
            format_offset(delta, zero="Z"),
            format_offset(delta),
            format_offset(delta, style="compact"),
            format_offset(delta, style="short"),
        ]
        assert mine[index] == result.split(" ")[index], (given, result)
