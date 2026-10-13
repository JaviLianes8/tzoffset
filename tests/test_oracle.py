"""The standard library as an oracle: strptime, strftime, isoformat, fromisoformat, zoneinfo."""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone

import pytest

from tzoffset import Grammar, OffsetError, Style, format_offset, parse_offset

MINUTES = [timedelta(minutes=m) for m in range(-1439, 1440)]
SECONDS = [timedelta(seconds=s) for s in range(-86399, 86400, 37)]
STYLES: list[Style] = ["colon", "compact", "short"]


def _aware(offset: timedelta) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone(offset))


@pytest.mark.parametrize("style", STYLES)
def test_every_offset_round_trips_through_every_style(style: Style) -> None:
    for offset in MINUTES + SECONDS:
        assert parse_offset(format_offset(offset, style=style)).utcoffset(None) == offset


@pytest.mark.parametrize(("grammar", "style"), [("rfc3339", "colon"), ("iso8601", "compact")])
def test_whole_minutes_round_trip_through_the_strict_grammars(
    grammar: Grammar, style: Style
) -> None:
    for offset in MINUTES:
        text = format_offset(offset, style=style)
        assert parse_offset(text, grammar=grammar).utcoffset(None) == offset


def test_compact_style_matches_strftime_z() -> None:
    for offset in MINUTES + SECONDS:
        assert format_offset(offset, style="compact") == _aware(offset).strftime("%z")


def test_colon_style_matches_isoformat() -> None:
    for offset in MINUTES + SECONDS:
        assert _aware(offset).isoformat().endswith(format_offset(offset))


def test_parse_agrees_with_strptime_z() -> None:
    for offset in MINUTES + SECONDS:
        for style in STYLES[:2]:
            text = format_offset(offset, style=style)
            expected = datetime.strptime(text, "%z").utcoffset()
            assert parse_offset(text).utcoffset(None) == expected, text


def _fuzz(seed: int, count: int) -> list[str]:
    rng = random.Random(seed)
    return [
        rng.choice("+-Z") + "".join(rng.choice("+-:0123569Z") for _ in range(rng.randint(0, 8)))
        for _ in range(count)
    ]


@pytest.mark.skipif(sys.version_info < (3, 11), reason="fromisoformat reads offsets from 3.11")
def test_whatever_parses_agrees_with_fromisoformat() -> None:
    # fromisoformat is looser (it takes minute 60 and fractions), so it only checks agreement.
    agreed = 0
    for text in _fuzz(seed=8601, count=60000):
        try:
            mine = parse_offset(text).utcoffset(None)
        except OffsetError:
            continue
        assert datetime.fromisoformat("2026-01-01T00:00" + text).utcoffset() == mine, text
        agreed += 1
    assert agreed > 500


def _zones() -> list[str]:
    zoneinfo = pytest.importorskip("zoneinfo")
    names = sorted(zoneinfo.available_timezones())
    if not names:  # pragma: no cover
        pytest.skip("no time zone database")
    return names


def test_every_zone_offset_formats_and_parses_back() -> None:
    from zoneinfo import ZoneInfo

    seen: set[timedelta] = set()
    for name in _zones():
        zone = ZoneInfo(name)
        for year in range(1800, 2050, 3):
            for month in (1, 7):
                moment = datetime(year, month, 1, tzinfo=zone)
                offset = moment.utcoffset()
                assert offset is not None
                text = format_offset(moment)
                assert parse_offset(text).utcoffset(None) == offset, (name, year)
                assert moment.isoformat().endswith(text), (name, year)
                seen.add(offset)
    assert max(seen) >= timedelta(hours=14)
    assert min(seen) <= timedelta(hours=-12)
    assert any(offset.seconds % 60 for offset in seen)
