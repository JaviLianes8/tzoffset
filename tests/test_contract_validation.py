"""Hand-written contracts for real types and inert type-name diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, tzinfo
from typing import cast

import pytest

from tzoffset import Grammar, Style, Zero, format_offset, is_unknown_local_offset, parse_offset

CALLS: list[Callable[[object], object]] = [
    lambda v: parse_offset(cast(str, v)),
    lambda v: is_unknown_local_offset(cast(str, v)),
    lambda v: parse_offset("Z", grammar=cast(Grammar, v)),
    lambda v: is_unknown_local_offset("Z", grammar=cast(Grammar, v)),
    lambda v: format_offset(cast(timedelta, v)),
    lambda v: format_offset(timedelta(0), style=cast(Style, v)),
    lambda v: format_offset(timedelta(0), zero=cast(Zero, v)),
]


class _ClassHook:
    @property  # type: ignore[misc]
    def __class__(self) -> type:
        raise AssertionError("class hook was called")


@pytest.mark.parametrize("call", CALLS)
def test_wrong_types_do_not_run_class_hooks(call: Callable[[object], object]) -> None:
    with pytest.raises(TypeError):
        call(_ClassHook())


def test_a_tzinfo_impostor_is_rejected_without_calling_it() -> None:
    class Pretender:
        __class__ = tzinfo  # type: ignore[assignment]

        def utcoffset(self, moment: datetime | None) -> timedelta:
            raise AssertionError("impostor callback was called")

    with pytest.raises(TypeError, match=r"not Pretender$"):
        format_offset(cast(tzinfo, Pretender()))


class _Name(str):
    def __len__(self) -> int:
        return 0

    def __str__(self) -> str:
        return "X" * 1_000_000

    def __format__(self, spec: str) -> str:
        return "X" * 1_000_000


class _Named(type):
    @property
    def __name__(cls) -> str:  # type: ignore[override]
        return _Name("ordinary")


class _Throwing(type):
    def __getattribute__(cls, name: str) -> object:
        if name == "__name__":
            raise AssertionError("name hook was called")
        return super().__getattribute__(name)


@pytest.mark.parametrize("call", CALLS)
@pytest.mark.parametrize("meta", [_Named, _Throwing])
def test_type_diagnostics_use_the_stored_type_name(
    call: Callable[[object], object],
    meta: type,
) -> None:
    value = meta("StoredName", (), {})()
    with pytest.raises(TypeError) as caught:
        call(value)
    assert str(caught.value).endswith("not StoredName")
    assert len(str(caught.value)) < 200


@pytest.mark.parametrize(
    "name",
    ["N" * 1_000_000, "\n\r\t\x1b" * 100, "\u202e" * 100],
    ids=["long", "controls", "unicode"],
)
def test_rendered_type_names_are_escaped_and_bounded(name: str) -> None:
    value = type(name, (), {})()
    with pytest.raises(TypeError) as caught:
        parse_offset(cast(str, value))
    message = str(caught.value)
    fragment = message.split("not ", 1)[1]
    assert len(fragment) <= 43
    assert message.isascii() and all(ord(char) >= 32 for char in message)


@pytest.mark.parametrize("answer", [None, object()])
def test_timezone_error_names_do_not_run_metaclass_hooks(answer: object) -> None:
    class Zone(tzinfo, metaclass=_Throwing):
        def utcoffset(self, moment: datetime | None) -> timedelta | None:
            return cast(timedelta | None, answer)

        def dst(self, moment: datetime | None) -> None:
            return None

        def tzname(self, moment: datetime | None) -> None:
            return None

    with pytest.raises((TypeError, ValueError)) as caught:
        format_offset(Zone())
    assert "Zone" in str(caught.value)
    assert len(str(caught.value)) < 200
