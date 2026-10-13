from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone, tzinfo

import pytest

from tzoffset import OffsetError, Style, Zero, format_offset, parse_offset


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
        format_offset(timezone.utc, style="iso")  # type: ignore[arg-type]


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


@pytest.mark.parametrize(
    ("style", "plus", "minus"),
    [("colon", "+00:00", "-00:00"), ("compact", "+0000", "-0000"), ("short", "+00", "-00")],
)
def test_format_zero_spellings(style: Style, plus: str, minus: str) -> None:
    assert format_offset(timedelta(0), style=style) == plus
    assert format_offset(timedelta(0), style=style, zero="+") == plus
    assert format_offset(timedelta(0), style=style, zero="-") == minus
    assert format_offset(timedelta(0), style=style, zero="Z") == "Z"


@pytest.mark.parametrize("zero", ["-", "Z"])
def test_format_zero_choice_leaves_other_offsets_alone(zero: Zero) -> None:
    assert format_offset(timedelta(hours=1), zero=zero) == "+01:00"
    assert format_offset(timedelta(seconds=-1), zero=zero) == "-00:00:01"


def test_format_rejects_unknown_zero() -> None:
    with pytest.raises(OffsetError, match="zero"):
        format_offset(timedelta(0), zero="z")  # type: ignore[arg-type]


def test_format_aware_datetime() -> None:
    moment = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=-3, minutes=-30)))
    assert format_offset(moment) == "-03:30"


def test_format_rejects_naive_datetime() -> None:
    with pytest.raises(OffsetError, match="naive"):
        format_offset(datetime(2026, 1, 1))


class _Fixed(tzinfo):
    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=4)

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> None:
        return None


class _Varying(_Fixed):
    def utcoffset(self, dt: datetime | None) -> timedelta | None:  # type: ignore[override]
        return None if dt is None else timedelta(hours=1 if dt.month < 6 else 2)


def test_format_any_fixed_tzinfo() -> None:
    assert format_offset(_Fixed()) == "+04:00"


def test_format_tzinfo_without_fixed_offset_points_at_datetimes() -> None:
    with pytest.raises(OffsetError, match="aware datetime"):
        format_offset(_Varying())
    assert format_offset(datetime(2026, 7, 1, tzinfo=_Varying())) == "+02:00"


@pytest.mark.parametrize("value", [None, 3600, "+01:00", date(2026, 1, 1), time(12)])
def test_format_rejects_other_types(value: object) -> None:
    with pytest.raises(TypeError, match="timedelta, tzinfo or datetime"):
        format_offset(value)  # type: ignore[arg-type]


def test_format_largest_offsets() -> None:
    almost = timedelta(hours=24) - timedelta(seconds=1)
    assert format_offset(almost) == "+23:59:59"
    assert format_offset(-almost) == "-23:59:59"
    with pytest.raises(OffsetError):
        format_offset(-timedelta(hours=24))


def test_format_short_with_seconds_keeps_every_field() -> None:
    assert format_offset(timedelta(hours=1, seconds=5), style="short") == "+01:00:05"


def test_format_sub_second_negative_offset_is_rejected() -> None:
    with pytest.raises(OffsetError, match="whole number of seconds"):
        format_offset(timedelta(seconds=-1, microseconds=1))
