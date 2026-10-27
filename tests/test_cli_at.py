"""--at on every supported Python: RFC 3339 timestamps, leap seconds, fractions, clock changes."""

from __future__ import annotations

import re
import sys
import zoneinfo
from datetime import datetime, timedelta, timezone

import pytest
from conftest import source_text

from tzoffset._cli import main
from tzoffset._cli_zone import _extended, moment

UTC = timezone.utc


def _need_zones() -> None:
    try:
        zoneinfo.ZoneInfo("America/Los_Angeles")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no time zone database")


def _out(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    assert main(list(argv)) == 0
    return capsys.readouterr().out.strip()


def _err(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as stop:
        main(list(argv))
    assert stop.value.code == 2
    return capsys.readouterr().err


# The six timestamps of RFC 3339 section 5.8, https://www.rfc-editor.org/rfc/rfc3339.txt,
# with the UTC instant each one names; second 60 is read as second 59 of the same minute.
RFC3339_EXAMPLES = {
    "1985-04-12T23:20:50.52Z": datetime(1985, 4, 12, 23, 20, 50, 520000, UTC),
    "1996-12-19T16:39:57-08:00": datetime(1996, 12, 20, 0, 39, 57, tzinfo=UTC),
    "1996-12-20T00:39:57Z": datetime(1996, 12, 20, 0, 39, 57, tzinfo=UTC),
    "1990-12-31T23:59:60Z": datetime(1990, 12, 31, 23, 59, 59, tzinfo=UTC),
    "1990-12-31T15:59:60-08:00": datetime(1990, 12, 31, 23, 59, 59, tzinfo=UTC),
    "1937-01-01T12:00:27.87+00:20": datetime(1937, 1, 1, 11, 40, 27, 870000, UTC),
}


@pytest.mark.parametrize(("text", "instant"), RFC3339_EXAMPLES.items())
def test_rfc3339_examples_are_read_on_every_python(text: str, instant: datetime) -> None:
    assert moment(text) == instant


def test_every_timestamp_of_rfc3339_section_5_8_is_read() -> None:
    text = source_text("rfc3339.txt")
    start = text.rindex("5.8. Examples")
    section = text[start : text.index("6. References", start)]
    stamps = re.findall(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)", section)
    assert len(stamps) == 6
    assert set(stamps) == set(RFC3339_EXAMPLES)
    for stamp in stamps:
        assert moment(stamp).tzinfo is not None


@pytest.mark.parametrize("text", list(RFC3339_EXAMPLES))
def test_rfc3339_examples_work_from_the_command_line(
    capsys: pytest.CaptureFixture[str], text: str
) -> None:
    _need_zones()
    assert _out(capsys, "--zone", "America/Los_Angeles", "--at", text) == "-08:00"


@pytest.mark.parametrize(
    ("text", "microsecond"),
    [("12:00:00.5", 500000), ("12:00:00,25", 250000), ("12:00:00.1234567", 123456)],
)
def test_any_fraction_of_a_second_is_read(text: str, microsecond: int) -> None:
    assert moment(f"2026-07-01T{text}").microsecond == microsecond
    assert moment(f"2026-07-01T{text}+09:00").utcoffset() == timedelta(hours=9)


@pytest.mark.parametrize(
    ("text", "spelled"),
    [
        ("2026-07-01T12:00:00.5", "2026-07-01T12:00:00.500000"),
        ("2026-07-01t12:00:00,25", "2026-07-01t12:00:00.250000"),
        ("2026-07-01 12:00:60.1234567", "2026-07-01 12:00:59.123456"),
        ("2026-07-01T12:00:00", "2026-07-01T12:00:00"),
        ("2026-07-01T12:00", "2026-07-01T12:00"),
    ],
)
def test_seconds_are_spelled_the_way_python_3_10_reads_them(text: str, spelled: str) -> None:
    # fromisoformat of 3.11 and later reads every input here; 3.10 only the spelled forms.
    assert _extended(text) == spelled


def test_a_naive_leap_second_is_read_as_second_59() -> None:
    assert moment("2016-12-31 23:59:60") == datetime(2016, 12, 31, 23, 59, 59)
    assert moment("2016-12-31T23:59:60.5") == datetime(2016, 12, 31, 23, 59, 59, 500000)


def test_unreadable_text_is_not_called_invalid_iso_8601(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _need_zones()
    err = _err(capsys, "--zone", "UTC", "--at", "noon")
    assert "cannot read --at as a date and time: 'noon'" in err
    assert "ISO 8601" not in err


def test_the_basic_form_follows_the_running_python(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    argv = ["--zone", "Asia/Tokyo", "--at", "20260701T120000Z"]
    if sys.version_info >= (3, 11):
        assert _out(capsys, *argv) == "+09:00"
    else:
        assert "cannot read --at" in _err(capsys, *argv)


@pytest.mark.parametrize(("zone", "expected"), [("Asia/Tokyo", "+09:00"), ("Etc/GMT-14", "+14:00")])
def test_zone_without_at_is_the_offset_in_that_zone_now(
    capsys: pytest.CaptureFixture[str], zone: str, expected: str
) -> None:
    # Both zones have kept one offset for decades, so the real clock gives a known answer.
    _need_zones()
    assert _out(capsys, "--zone", zone) == expected


@pytest.mark.parametrize(
    ("at", "expected"),
    [
        ("2026-10-25T02:30", "+02:00"),  # repeated: the first pass, still summer time
        ("2026-03-29T02:30", "+01:00"),  # skipped: the offset before the change
        ("2026-10-25T01:59", "+02:00"),
        ("2026-10-25T03:00", "+01:00"),
    ],
)
def test_a_repeated_or_skipped_wall_time_takes_the_offset_before_the_change(
    capsys: pytest.CaptureFixture[str], at: str, expected: str
) -> None:
    _need_zones()
    assert _out(capsys, "--zone", "Europe/Madrid", "--at", at) == expected
