"""The complete promise of every public name: signature, result types and failure types."""

from __future__ import annotations

import inspect
import typing
from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone, tzinfo

import pytest

import tzoffset
from tzoffset import OffsetError, format_offset, is_unknown_local_offset, parse_offset

SIGNATURES = {
    "parse_offset": "(text: 'str', *, grammar: 'Grammar' = 'lenient') -> 'timezone'",
    "is_unknown_local_offset": "(text: 'str', *, grammar: 'Grammar' = 'lenient') -> 'bool'",
    "format_offset": "(value: 'timedelta | tzinfo | datetime', *, style: 'Style' = 'colon', "
    "zero: 'Zero' = '+') -> 'str'",
}


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_function_signatures_are_pinned(name: str) -> None:
    assert str(inspect.signature(getattr(tzoffset, name))) == SIGNATURES[name]


def test_annotations_resolve_to_real_types() -> None:
    hints = typing.get_type_hints(format_offset)
    assert hints["value"] == timedelta | tzinfo | datetime
    assert hints["style"] == tzoffset.Style and hints["zero"] == tzoffset.Zero
    assert typing.get_type_hints(parse_offset)["return"] is timezone


def test_every_public_name_is_documented_with_an_example() -> None:
    for name in tzoffset.__all__:
        doc = inspect.getdoc(getattr(tzoffset, name)) or ""
        assert ">>> " in doc, name


def test_results_have_exact_types() -> None:
    assert type(parse_offset("+05:30")) is timezone
    assert parse_offset("+00:00") is timezone.utc and parse_offset("-00") is timezone.utc
    assert type(format_offset(timedelta(hours=1))) is str
    assert type(is_unknown_local_offset("Z")) is bool


class _Hostile(str):
    """A str subclass whose methods lie; only its characters may count."""

    def strip(self, chars: str | None = None) -> str:
        return "+09:00"

    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        raise AssertionError("repr of the caller's object was used")


def test_str_subclasses_are_read_by_their_characters() -> None:
    assert parse_offset(_Hostile(" +05:30 ")) == timezone(timedelta(hours=5, minutes=30))
    with pytest.raises(OffsetError, match="'bogus'"):
        parse_offset(_Hostile("bogus"))
    with pytest.raises(OffsetError, match="unknown grammar: 'x'"):
        parse_offset("+01", grammar=_Hostile("x"))  # type: ignore[arg-type]
    assert format_offset(timedelta(0), style=_Hostile("short"), zero=_Hostile("-")) == "-00"  # type: ignore[arg-type]


class _Plain(tzinfo):
    """A tzinfo with the abstract methods filled in; subclasses choose utcoffset."""

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> None:
        return None


class _Returns(_Plain):
    def __init__(self, value: object) -> None:
        self.value = value

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return self.value  # type: ignore[return-value]


# Untyped handles, so the type checker lets the keyword-only options be passed by position.
_UNCHECKED_PARSE: Callable[..., object] = parse_offset
_UNCHECKED_FORMAT: Callable[..., object] = format_offset

WRONG_TYPES: list[Callable[[], object]] = [
    lambda: parse_offset(None),  # type: ignore[arg-type]
    lambda: parse_offset(b"+05:30"),  # type: ignore[arg-type]
    lambda: parse_offset("+05:30", grammar=None),  # type: ignore[arg-type]
    lambda: parse_offset("+05:30", grammar=1),  # type: ignore[arg-type]
    lambda: is_unknown_local_offset(5),  # type: ignore[arg-type]
    lambda: is_unknown_local_offset("Z", grammar=b"lenient"),  # type: ignore[arg-type]
    lambda: format_offset(3600),  # type: ignore[arg-type]
    lambda: format_offset(None),  # type: ignore[arg-type]
    lambda: format_offset(date(2026, 1, 1)),  # type: ignore[arg-type]
    lambda: format_offset(time(12, tzinfo=timezone.utc)),  # type: ignore[arg-type]
    lambda: format_offset(timedelta(0), style=None),  # type: ignore[arg-type]
    lambda: format_offset(timedelta(0), zero=0),  # type: ignore[arg-type]
    lambda: format_offset(_Returns(3600)),
    lambda: format_offset(_Returns("+01:00")),
    lambda: _UNCHECKED_PARSE("+05:30", "rfc3339"),
    lambda: _UNCHECKED_FORMAT(timedelta(0), "short"),
]


@pytest.mark.parametrize("call", WRONG_TYPES)
def test_wrong_argument_types_raise_type_error(call: Callable[[], object]) -> None:
    with pytest.raises(TypeError):
        call()


BAD_VALUES: list[Callable[[], object]] = [
    lambda: parse_offset("+24:00"),
    lambda: parse_offset("+05:30", grammar="rfc2822"),  # type: ignore[arg-type]
    lambda: is_unknown_local_offset("-00:60"),
    lambda: format_offset(timedelta(hours=24)),
    lambda: format_offset(timedelta(seconds=1, microseconds=1)),
    lambda: format_offset(datetime(2026, 1, 1)),
    lambda: format_offset(_Returns(None)),
    lambda: format_offset(timedelta(0), style="iso"),  # type: ignore[arg-type]
    lambda: format_offset(timedelta(0), zero="z"),  # type: ignore[arg-type]
]


@pytest.mark.parametrize("call", BAD_VALUES)
def test_bad_values_raise_offset_error(call: Callable[[], object]) -> None:
    with pytest.raises(OffsetError):
        call()


def test_unknown_options_name_the_accepted_values() -> None:
    with pytest.raises(OffsetError, match=r"expected one of 'colon', 'compact', 'short'"):
        format_offset(timedelta(0), style="iso")  # type: ignore[arg-type]
    with pytest.raises(OffsetError, match=r"expected one of '\+', '-', 'Z'"):
        format_offset(timedelta(0), zero="z")  # type: ignore[arg-type]
    with pytest.raises(OffsetError, match=r"expected one of 'lenient', 'rfc3339', 'iso8601'"):
        parse_offset("Z", grammar="RFC3339")  # type: ignore[arg-type]


class _LongName(_Plain):
    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def __repr__(self) -> str:
        return "R" * 1_000_000


_LongName.__name__ = "N" * 10_000

HUGE = "9" * 1_000_000
MESSAGES: list[Callable[[], object]] = [
    lambda: parse_offset(HUGE),
    lambda: parse_offset("+" + HUGE, grammar="iso8601"),
    lambda: is_unknown_local_offset(" " * 500_000 + "+25:00" + " " * 500_000),
    lambda: parse_offset("+01", grammar=HUGE),  # type: ignore[arg-type]
    lambda: format_offset(timedelta(0), style=HUGE),  # type: ignore[arg-type]
    lambda: format_offset(_LongName()),
    lambda: format_offset(_Returns(_LongName())),
    lambda: format_offset(_LongName),  # type: ignore[arg-type]
    lambda: format_offset(timedelta(days=999_999_999)),
]


@pytest.mark.parametrize("call", MESSAGES)
def test_messages_never_echo_huge_input(call: Callable[[], object]) -> None:
    with pytest.raises((OffsetError, TypeError)) as caught:
        call()
    assert len(str(caught.value)) < 200, str(caught.value)[:300]


def test_a_long_text_is_quoted_by_its_first_forty_characters() -> None:
    with pytest.raises(OffsetError) as caught:
        parse_offset("+05:30" + "x" * 100)
    assert str(caught.value) == (
        "not a valid lenient UTC offset: '+05:30" + "x" * 34 + "'... (106 characters)"
    )
