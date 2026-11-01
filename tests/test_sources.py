"""Ground truth from the fetched RFC 3339 and RFC 9557 texts (python scripts/fetch_vectors.py).

Phrases and examples are cut from the texts fetched from
https://www.rfc-editor.org/rfc/rfc3339.txt, https://www.rfc-editor.org/rfc/rfc5322.txt and
https://www.rfc-editor.org/rfc/rfc9557.txt (fetched 2026-10-18 and again 2026-10-27, checked
against MANIFEST.txt); the expected values come from the RFCs, not from this library.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import SOURCES, source_bytes, source_text

from tzoffset import Grammar, OffsetError, format_offset, is_unknown_local_offset, parse_offset

STAMP = r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)(Z|[+-]\d\d:\d\d)"


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


def test_rfc3339_offset_grammar_is_the_one_implemented() -> None:
    text = source_text("rfc3339.txt")
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


def test_rfc3339_section_4_2_subtracts_the_offset() -> None:
    text = source_text("rfc3339.txt")
    found = re.search(
        r"(\d\d:\d\d:\d\d)([+-]\d\d:\d\d) is the same time as (\d\d:\d\d:\d\d)Z", text
    )
    assert found is not None
    local, offset, utc = found.groups()
    moment = datetime.fromisoformat(f"2026-01-01T{local}").replace(
        tzinfo=parse_offset(offset, grammar="rfc3339")
    )
    assert moment.astimezone(timezone.utc).time().isoformat() == utc


def test_rfc3339_section_5_8_examples() -> None:
    text = source_text("rfc3339.txt")
    start = text.rindex("5.8. Examples")  # the first one is in the table of contents
    section = text[start : text.index("6. References", start)]
    stamps = re.findall(STAMP, section)
    assert len(stamps) == 6
    for _, offset in stamps:
        assert format_offset(parse_offset(offset, grammar="rfc3339"), zero="Z") == offset
    # "1996-12-19T16:39:57-08:00 ... Note that this is equivalent to 1996-12-20T00:39:57Z"
    no_stamp = r"(?:(?!\d{4}-\d\d-\d\dT).)*?"
    pair = re.search(STAMP + " This represents" + no_stamp + "equivalent to " + STAMP, section)
    assert pair is not None
    local, offset, utc, zulu = pair.groups()
    moment = datetime.fromisoformat(local).replace(tzinfo=parse_offset(offset))
    assert moment.astimezone(timezone.utc) == datetime.fromisoformat(utc).replace(
        tzinfo=parse_offset(zulu)
    )


def test_rfc3339_netherlands_example_needs_seconds() -> None:
    text = source_text("rfc3339.txt")
    found = re.search(r"exactly (\d+) minutes and (\d+)\.(\d+) seconds ahead of UTC", text)
    assert found is not None
    minutes, seconds, hundredths = (int(group) for group in found.groups())
    exact = timedelta(minutes=minutes, seconds=seconds, milliseconds=10 * hundredths)
    # A fraction of a second has no offset spelling; the whole seconds need a seconds field.
    with pytest.raises(OffsetError, match="whole number of seconds"):
        format_offset(exact)
    whole = timedelta(minutes=minutes, seconds=seconds)
    assert format_offset(whole) == f"+00:{minutes:02d}:{seconds:02d}"
    # "this timestamp uses the closest representable UTC offset": the example's +00:20.
    closest = timedelta(minutes=round(exact / timedelta(minutes=1)))
    stamp = re.search(STAMP + " This represents the same instant of time as noon, January 1", text)
    assert stamp is not None
    assert format_offset(closest) == stamp.group(2)


def test_rfc9557_reads_z_like_negative_zero() -> None:
    text = source_text("rfc9557.txt")
    assert "interpreting the offset Z to mean the same as -00:00" in text
    assert "[ISO8601:2000] and later do not allow -00:00" in text
    assert "Note that the semantics of the local offset +00:00 is not updated" in text
    assert "-00:00 may be used instead of Z because they have the same meaning" in text
    assert is_unknown_local_offset("Z") and is_unknown_local_offset("-00:00")
    assert not is_unknown_local_offset("+00:00")
    with pytest.raises(OffsetError):
        parse_offset("-00:00", grammar="iso8601")
    assert parse_offset("Z", grammar="iso8601") is timezone.utc


def test_rfc9557_offset_time_zone_example() -> None:
    text = source_text("rfc9557.txt")
    found = re.search(r"specific UTC offset, e\.g\., ([+-]\d\d:\d\d)", text)
    assert found is not None
    offset = found.group(1)
    assert f"{offset}[{offset}]" in text
    assert format_offset(parse_offset(offset, grammar="rfc3339")) == offset


def _zones() -> object:
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        zoneinfo.ZoneInfo("Europe/Paris")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no time zone database")
    return zoneinfo


def test_rfc9557_paris_example_through_the_tz_database() -> None:
    zoneinfo = _zones()
    text = source_text("rfc9557.txt")
    found = re.search(STAMP + r"\[Europe/Paris\][\s|]*does not exhibit", text)
    assert found is not None
    same = re.search(r"it is equivalent to:[\s|]*" + STAMP + r"\[Europe/Paris\]", text)
    assert same is not None
    utc = datetime.fromisoformat(found.group(1)).replace(tzinfo=parse_offset(found.group(2)))
    paris = utc.astimezone(zoneinfo.ZoneInfo("Europe/Paris"))  # type: ignore[attr-defined]
    assert format_offset(paris) == same.group(2)
    assert paris.replace(tzinfo=None).isoformat() == same.group(1)


def test_rfc9557_new_york_winter_offset() -> None:
    zoneinfo = _zones()
    text = source_text("rfc9557.txt")
    found = re.search(
        r"wintertime in (\d{4}) was \d hours behind UTC, so its UTC offset was (\S+)\.", text
    )
    assert found is not None
    year, offset = int(found.group(1)), found.group(2)
    new_york = zoneinfo.ZoneInfo("America/New_York")  # type: ignore[attr-defined]
    assert format_offset(datetime(year, 1, 15, 12, tzinfo=new_york)) == offset


def test_a_tampered_source_fails_instead_of_passing(tmp_path: Path) -> None:
    body = bytearray(source_bytes("rfc3339.txt"))
    body[1000] ^= 1
    (tmp_path / "MANIFEST.txt").write_bytes((SOURCES / "MANIFEST.txt").read_bytes())
    (tmp_path / "rfc3339.txt").write_bytes(bytes(body))
    with pytest.raises(AssertionError, match="differs from MANIFEST"):
        source_bytes("rfc3339.txt", folder=tmp_path)


def test_rfc5322_zone_is_signed_hhmm_and_minus_zero_means_unknown() -> None:
    # https://www.rfc-editor.org/rfc/rfc5322.txt, section 3.3 (fetched 2026-10-18 and 2026-10-27)
    text = source_text("rfc5322.txt")
    assert 'zone = (FWS ( "+" / "-" ) 4DIGIT) / obs-zone' in text
    assert "+hhmm means +(hh * 60 + mm) minutes, and -hhmm means -(hh * 60 + mm) minutes" in text
    assert 'Though "-0000" also indicates Universal Time' in text
    for hh, mm in [(0, 0), (5, 30), (9, 45), (12, 0), (23, 59)]:
        for sign in (1, -1):
            spelled = f"{'+' if sign > 0 else '-'}{hh:02d}{mm:02d}"
            delta = timedelta(minutes=sign * (hh * 60 + mm))
            assert (
                parse_offset(spelled, grammar="iso8601" if delta else "lenient").utcoffset(None)
                == delta
            )
            if delta:
                assert format_offset(delta, style="compact") == spelled
    assert is_unknown_local_offset("-0000") and not is_unknown_local_offset("+0000")
    assert format_offset(timedelta(0), style="compact", zero="-") == "-0000"
