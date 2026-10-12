from datetime import timedelta, timezone

import pytest

from tzoffset import OffsetError, format_offset, parse_offset


def test_format_colon_style() -> None:
    assert format_offset(timezone(timedelta(hours=5, minutes=30))) == "+05:30"


def test_format_compact_style() -> None:
    assert format_offset(timezone(timedelta(hours=5, minutes=30)), style="compact") == "+0530"


def test_format_short_style_drops_zero_minutes() -> None:
    assert format_offset(timezone(timedelta(hours=9)), style="short") == "+09"


def test_format_short_style_keeps_minutes_when_present() -> None:
    assert format_offset(timezone(timedelta(hours=5, minutes=30)), style="short") == "+05:30"


def test_format_negative_offset() -> None:
    assert format_offset(timezone(timedelta(hours=-8))) == "-08:00"


def test_format_utc_is_positive_zero() -> None:
    assert format_offset(timezone.utc) == "+00:00"


def test_format_accepts_timedelta() -> None:
    assert format_offset(timedelta(hours=-2, minutes=-30)) == "-02:30"


def test_format_includes_seconds() -> None:
    assert format_offset(timedelta(hours=5, minutes=30, seconds=45)) == "+05:30:45"


def test_format_compact_includes_seconds() -> None:
    offset = timedelta(hours=5, minutes=30, seconds=45)
    assert format_offset(offset, style="compact") == "+053045"


def test_format_rejects_unknown_style() -> None:
    with pytest.raises(OffsetError):
        format_offset(timezone.utc, style="iso")


def test_format_rejects_sub_second_offset() -> None:
    with pytest.raises(OffsetError):
        format_offset(timedelta(hours=1, microseconds=500))


def test_format_rejects_out_of_range_offset() -> None:
    with pytest.raises(OffsetError):
        format_offset(timedelta(hours=24))


@pytest.mark.parametrize("text", ["Z", "+09", "-0800", "+05:30", "+00:00", "-02:30"])
def test_round_trip_parse_then_format(text: str) -> None:
    tz = parse_offset(text)
    assert parse_offset(format_offset(tz)) == tz
