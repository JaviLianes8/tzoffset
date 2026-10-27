"""The promise kept for unusual values: subclasses that lie, tzinfo results, exact messages."""

from __future__ import annotations

import typing
from datetime import datetime, timedelta, timezone, tzinfo

import pytest

import tzoffset
from tzoffset import OffsetError, format_offset, is_unknown_local_offset, parse_offset
from tzoffset._types import __test__ as alias_examples


def test_importing_leaves_the_shared_literal_objects_alone() -> None:
    # typing caches Literal[...] objects: a caller's alias of the same values is the very
    # same object, so the package must not give it a docstring of its own.
    mine = typing.Literal["+", "-", "Z"]
    assert mine is tzoffset.Zero
    fresh = typing.Literal["a value no other module uses"].__doc__
    for alias in (tzoffset.Grammar, tzoffset.Style, tzoffset.Zero):
        assert alias.__doc__ == fresh


def test_every_alias_has_a_documented_example() -> None:
    assert sorted(alias_examples) == ["Grammar", "Style", "Zero"]
    for name, text in alias_examples.items():
        assert ">>> " in text and f"from tzoffset import {name}" in text, name


class _Fixed(tzinfo):
    def __init__(self, offset: object) -> None:
        self.offset = offset

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return self.offset  # type: ignore[return-value]

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> None:
        return None


@pytest.mark.parametrize(
    "offset", [timedelta(days=2), timedelta(hours=25), timedelta(hours=-24), timedelta.max]
)
def test_a_datetime_with_an_offset_of_a_day_or_more_is_an_offset_error(offset: timedelta) -> None:
    for value in (_Fixed(offset), datetime(2026, 1, 1, tzinfo=_Fixed(offset))):
        with pytest.raises(OffsetError) as caught:
            format_offset(value)
        assert len(str(caught.value)) < 200


def test_a_datetime_whose_tzinfo_returns_a_non_timedelta_is_a_type_error() -> None:
    with pytest.raises(TypeError, match=r"_Fixed\.utcoffset\(a datetime\) returned str"):
        format_offset(datetime(2026, 1, 1, tzinfo=_Fixed("+01:00")))
    with pytest.raises(TypeError, match=r"_Fixed\.utcoffset\(None\) returned int"):
        format_offset(_Fixed(3600))


class _OwnOffset(datetime):
    """A datetime whose own utcoffset lies; only its stored tzinfo may count."""

    def utcoffset(self) -> timedelta:
        return "+05:00"  # type: ignore[return-value]


def test_a_datetime_subclass_is_read_by_its_stored_tzinfo() -> None:
    with pytest.raises(OffsetError, match="naive datetime"):
        format_offset(_OwnOffset(2026, 1, 1))
    assert format_offset(_OwnOffset(2026, 1, 1, tzinfo=timezone.utc)) == "+00:00"
    plus_two = timezone(timedelta(hours=2))
    assert format_offset(_OwnOffset(2026, 1, 1, tzinfo=plus_two)) == "+02:00"


class _OwnTzinfo(datetime):
    """A datetime whose tzinfo attribute lies about the stored one."""

    @property
    def tzinfo(self) -> timezone:
        return timezone(timedelta(hours=5))


def test_a_datetime_subclass_cannot_swap_its_tzinfo() -> None:
    assert format_offset(_OwnTzinfo(2026, 1, 1, tzinfo=timezone.utc)) == "+00:00"
    with pytest.raises(OffsetError, match="naive datetime"):
        format_offset(_OwnTzinfo(2026, 1, 1))


class _Lie(timedelta):
    """A timedelta whose fields and repr lie; only the stored value may count."""

    @property
    def seconds(self) -> int:
        return 3600

    @property
    def days(self) -> int:
        return 0.5  # type: ignore[return-value]

    @property
    def microseconds(self) -> int:
        return 7

    def __repr__(self) -> str:
        return "R" * 1_000_000


def test_a_timedelta_subclass_is_read_by_its_stored_value() -> None:
    assert format_offset(_Lie(0)) == "+00:00"
    assert format_offset(_Lie(hours=1)) == "+01:00"
    assert format_offset(_Fixed(_Lie(minutes=-30))) == "-00:30"
    assert format_offset(datetime(2026, 1, 1, tzinfo=_Fixed(_Lie(hours=9)))) == "+09:00"


class _LongIso(datetime):
    def isoformat(self, sep: str = "T", timespec: str = "auto") -> str:
        return "I" * 1_000_000


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            _Lie(days=2),
            "offset out of range: datetime.timedelta(days=2) (it must be under one day)",
        ),
        (
            _Lie(microseconds=5),
            "offset is not a whole number of seconds: datetime.timedelta(microseconds=5)",
        ),
        (_LongIso(2026, 1, 1), "a naive datetime has no UTC offset: 2026-01-01T00:00:00"),
        (
            timedelta.max,
            "offset is not a whole number of seconds: "
            "datetime.timedelta(days=999999999, seconds=86399, microseconds=999999)",
        ),
    ],
)
def test_offset_messages_show_the_exact_value(value: object, message: str) -> None:
    with pytest.raises(OffsetError) as caught:
        format_offset(value)  # type: ignore[arg-type]
    assert str(caught.value) == message


def test_a_text_of_forty_characters_is_quoted_whole() -> None:
    with pytest.raises(OffsetError) as caught:
        parse_offset("x" * 40)
    assert str(caught.value) == f"not a valid lenient UTC offset: {'x' * 40!r}"
    with pytest.raises(OffsetError) as caught:
        parse_offset("x" * 41)
    assert str(caught.value) == f"not a valid lenient UTC offset: {'x' * 40!r}... (41 characters)"


def test_type_errors_name_the_parameter() -> None:
    with pytest.raises(TypeError) as caught:
        parse_offset(5)  # type: ignore[arg-type]
    assert str(caught.value) == "text must be a str, not int"
    with pytest.raises(TypeError) as caught:
        is_unknown_local_offset(b"Z")  # type: ignore[arg-type]
    assert str(caught.value) == "text must be a str, not bytes"
    with pytest.raises(TypeError) as caught:
        parse_offset("Z", grammar=None)  # type: ignore[arg-type]
    assert str(caught.value) == "grammar must be a str, not NoneType"
    with pytest.raises(TypeError) as caught:
        format_offset(timedelta(0), style=1)  # type: ignore[arg-type]
    assert str(caught.value) == "style must be a str, not int"
    with pytest.raises(TypeError) as caught:
        format_offset(timedelta(0), zero=0)  # type: ignore[arg-type]
    assert str(caught.value) == "zero must be a str, not int"
