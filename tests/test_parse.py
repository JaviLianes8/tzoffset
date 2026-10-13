from __future__ import annotations

from datetime import timedelta, timezone

import pytest

from tzoffset import OffsetError, parse_offset


def test_parse_z_is_utc() -> None:
    assert parse_offset("Z") == timezone.utc


def test_parse_lowercase_z_is_utc() -> None:
    assert parse_offset("z") == timezone.utc


def test_parse_colon_form() -> None:
    assert parse_offset("+05:30") == timezone(timedelta(hours=5, minutes=30))


def test_parse_compact_form() -> None:
    assert parse_offset("-0800") == timezone(timedelta(hours=-8))


def test_parse_hours_only() -> None:
    assert parse_offset("+09") == timezone(timedelta(hours=9))


def test_parse_with_seconds_colon() -> None:
    assert parse_offset("+05:30:45") == timezone(timedelta(hours=5, minutes=30, seconds=45))


def test_parse_with_seconds_compact() -> None:
    assert parse_offset("-053045") == timezone(timedelta(hours=-5, minutes=-30, seconds=-45))


def test_parse_negative_offset() -> None:
    assert parse_offset("-02:30") == timezone(timedelta(hours=-2, minutes=-30))


def test_parse_strips_surrounding_whitespace() -> None:
    assert parse_offset("  +01:00  ") == timezone(timedelta(hours=1))


@pytest.mark.parametrize(
    "text",
    [
        "",
        "+5",
        "0530",
        "+05:70",
        "+05:30:99",
        "+24:00",
        "+2530",
        "+05-30",
        "++05",
        "0800",
        "+05:3045",
    ],
)
def test_parse_rejects_invalid(text: str) -> None:
    with pytest.raises(OffsetError):
        parse_offset(text)


def test_parse_returns_the_utc_singleton_for_zero() -> None:
    assert parse_offset("+00:00") is timezone.utc
    assert parse_offset("-00:00") is timezone.utc


def test_parse_largest_offsets() -> None:
    assert parse_offset("+23:59:59") == timezone(timedelta(hours=24) - timedelta(seconds=1))
    assert parse_offset("-23:59:59") == timezone(timedelta(seconds=1) - timedelta(hours=24))


@pytest.mark.parametrize("value", [None, 5, b"+05:00", timedelta(hours=1)])
def test_parse_rejects_non_strings(value: object) -> None:
    with pytest.raises(TypeError, match="must be a str"):
        parse_offset(value)  # type: ignore[arg-type]


def test_parse_rejects_unicode_digits() -> None:
    with pytest.raises(OffsetError):
        parse_offset("+\u0660\u0665:30")


def test_lenient_strips_ascii_whitespace_only() -> None:
    assert parse_offset("\t+05:30\r\n\x0b\x0c ") == timezone(timedelta(hours=5, minutes=30))
    for space in ("\u3000", "\u00a0", "\u2003", "\x85"):
        with pytest.raises(OffsetError):
            parse_offset(space + "+05:30")
