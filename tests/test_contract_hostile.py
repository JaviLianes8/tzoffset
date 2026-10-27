"""The promise kept for hostile values: impostors, operator overrides, tzinfo that change."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from unittest import mock

import pytest

from tzoffset import OffsetError, format_offset


class _Answers(tzinfo):
    """A tzinfo whose utcoffset returns the given answers in turn, then the last one."""

    def __init__(self, *answers: object) -> None:
        self.answers = list(answers)

    def utcoffset(self, dt: datetime | None) -> timedelta:
        answer = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        return answer  # type: ignore[return-value]

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> None:
        return None


@pytest.mark.parametrize("later", [timedelta(days=2), timedelta(hours=-24), "+01:00", 3600])
def test_a_naive_message_does_not_ask_the_tzinfo_again(later: object) -> None:
    # The first answer (None) decides; a second call could raise the standard library's
    # ValueError or TypeError instead of the documented OffsetError.
    zone = _Answers(None, later)
    with pytest.raises(OffsetError) as caught:
        format_offset(datetime(2026, 1, 1, 12, 30, tzinfo=zone))
    assert str(caught.value) == "a naive datetime has no UTC offset: 2026-01-01T12:30:00"
    assert zone.answers == [later]


def test_a_naive_message_shows_the_stored_fields() -> None:
    with pytest.raises(OffsetError) as caught:
        format_offset(datetime(1, 2, 3, 4, 5, 6, 7, fold=1, tzinfo=_Answers(None)))
    assert str(caught.value) == "a naive datetime has no UTC offset: 0001-02-03T04:05:06.000007"


def _impostors() -> list[object]:
    # Mock(spec=...) passes isinstance through a spoofed __class__ without being one.
    return [mock.Mock(spec=timedelta), mock.NonCallableMock(spec=timedelta)]


@pytest.mark.parametrize("fake", _impostors())
def test_an_impostor_timedelta_is_a_type_error(fake: object) -> None:
    with pytest.raises(TypeError, match=r"not (Mock|NonCallableMock)$"):
        format_offset(fake)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"_Answers\.utcoffset\(None\) returned"):
        format_offset(_Answers(fake))
    with pytest.raises(TypeError, match=r"_Answers\.utcoffset\(a datetime\) returned"):
        format_offset(datetime(2026, 1, 1, tzinfo=_Answers(fake)))


def test_an_impostor_datetime_is_a_type_error() -> None:
    with pytest.raises(TypeError) as caught:
        format_offset(mock.Mock(spec=datetime))
    assert str(caught.value) == "expected a timedelta, tzinfo or datetime, not Mock"


class _Arith(timedelta):
    """A timedelta whose arithmetic lies; only the stored value may count."""

    def __add__(self, other: object) -> timedelta:
        return timedelta(hours=2)

    def __radd__(self, other: object) -> timedelta:
        return timedelta(hours=1)

    def __neg__(self) -> timedelta:
        return timedelta(hours=3)

    def __abs__(self) -> timedelta:
        return timedelta(hours=4)


def test_a_timedelta_subclass_arithmetic_is_never_used() -> None:
    assert format_offset(_Arith(hours=5)) == "+05:00"
    assert format_offset(_Arith(hours=-5, minutes=-30)) == "-05:30"
    assert format_offset(_Answers(_Arith(hours=5))) == "+05:00"
    assert format_offset(datetime(2026, 1, 1, tzinfo=_Answers(_Arith(hours=5)))) == "+05:00"
    assert format_offset(datetime(2026, 1, 1, tzinfo=timezone(_Arith(hours=5)))) == "+05:00"
