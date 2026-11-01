"""Exact option spellings and stored string contents, derived from the public contract."""

from __future__ import annotations

from datetime import timedelta, timezone
from typing import cast

import pytest

from tzoffset import (
    Grammar,
    OffsetError,
    Style,
    Zero,
    format_offset,
    is_unknown_local_offset,
    parse_offset,
)


@pytest.mark.parametrize("padding", [" ", "\t", "\n", "\r", "\f", "\v", "\u00a0"])
@pytest.mark.parametrize("leading", [True, False])
def test_padded_option_values_are_rejected(padding: str, leading: bool) -> None:
    def padded(value: str) -> str:
        return padding + value if leading else value + padding

    for grammar in ("lenient", "rfc3339", "iso8601"):
        for reader in (parse_offset, is_unknown_local_offset):
            with pytest.raises(OffsetError, match="unknown grammar"):
                reader("Z", grammar=cast(Grammar, padded(grammar)))
    for style in ("colon", "compact", "short"):
        with pytest.raises(OffsetError, match="unknown style"):
            format_offset(timedelta(0), style=cast(Style, padded(style)))
    for zero in ("+", "-", "Z"):
        with pytest.raises(OffsetError, match="unknown zero"):
            format_offset(timedelta(0), zero=cast(Zero, padded(zero)))


class _Converted(str):
    calls = 0

    def __str__(self) -> str:
        type(self).calls += 1
        return "Z"


def test_parsing_and_unknown_detection_never_call_string_conversion() -> None:
    _Converted.calls = 0
    assert parse_offset(_Converted("+05:30")) == timezone(timedelta(hours=5, minutes=30))
    assert not is_unknown_local_offset(_Converted("+00:00"))
    assert is_unknown_local_offset(_Converted("-00:00"))
    assert _Converted.calls == 0


def test_option_validation_never_calls_string_conversion() -> None:
    _Converted.calls = 0
    assert parse_offset("+01", grammar=cast(Grammar, _Converted("lenient"))).utcoffset(
        None
    ) == timedelta(hours=1)
    assert not is_unknown_local_offset("+01:00", grammar=cast(Grammar, _Converted("rfc3339")))
    assert (
        format_offset(
            timedelta(0), style=cast(Style, _Converted("short")), zero=cast(Zero, _Converted("-"))
        )
        == "-00"
    )
    with pytest.raises(OffsetError, match="unknown zero"):
        format_offset(timedelta(0), zero=cast(Zero, _Converted("invalid")))
    assert _Converted.calls == 0
