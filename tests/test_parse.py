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
