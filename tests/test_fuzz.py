"""Seeded fuzzing and property tests: only the documented errors, no hang, linear time."""

from __future__ import annotations

import random
import time
from datetime import timedelta

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

GRAMMARS: list[Grammar] = ["lenient", "rfc3339", "iso8601"]
STYLES: list[Style] = ["colon", "compact", "short"]
ZEROS: list[Zero] = ["+", "-", "Z"]
# Offset characters, their look-alikes (Unicode digits, minus sign, full-width plus,
# no-break space) and control characters.
LOOK_ALIKES = "".join(map(chr, (0x0660, 0x0665, 0x0966, 0x2212, 0xFF0B, 0x00A0)))
ALPHABET = "+-:Zz0123456789 \t\n\x00.,T" + LOOK_ALIKES


def _texts(seed: int, count: int) -> list[str]:
    rng = random.Random(seed)
    texts = []
    for _ in range(count):
        size = rng.choice([0, 1, 2, 3, 5, 6, 7, 9, 10, rng.randint(0, 40)])
        texts.append("".join(rng.choice(ALPHABET) for _ in range(size)))
    return texts


@pytest.mark.parametrize("grammar", GRAMMARS)
def test_random_text_parses_or_raises_offset_error(grammar: Grammar) -> None:
    accepted = 0
    for text in _texts(seed=3339 + len(grammar), count=40_000):
        try:
            zone = parse_offset(text, grammar=grammar)
        except OffsetError:
            with pytest.raises(OffsetError):
                is_unknown_local_offset(text, grammar=grammar)
            continue
        accepted += 1
        offset = zone.utcoffset(None)
        assert offset is not None and abs(offset) < timedelta(days=1), text
        assert text.isascii(), text
        # What parses formats back and parses again to the same offset.
        assert parse_offset(format_offset(zone)).utcoffset(None) == offset, text
        assert is_unknown_local_offset(text, grammar=grammar) in (True, False)
    assert accepted > 10


def test_random_offsets_round_trip_in_every_style_and_zero() -> None:
    rng = random.Random(9557)
    for _ in range(20_000):
        offset = timedelta(seconds=rng.randint(-86_399, 86_399))
        for style in STYLES:
            for zero in ZEROS:
                text = format_offset(offset, style=style, zero=zero)
                assert parse_offset(text).utcoffset(None) == offset, (offset, text)
                assert is_unknown_local_offset(text) == (offset == timedelta(0) and zero != "+")
                if offset.seconds % 60 == 0 and style == "colon":
                    parsed = parse_offset(text, grammar="rfc3339")
                    assert parsed.utcoffset(None) == offset


def test_random_out_of_range_offsets_raise_offset_error() -> None:
    rng = random.Random(8601)
    for _ in range(5_000):
        days = rng.choice([1, -1]) * rng.randint(1, 999_999_999)
        offset = timedelta(days=days, seconds=rng.randint(0, 86_399))
        with pytest.raises(OffsetError):
            format_offset(offset)
        with pytest.raises(OffsetError):
            format_offset(timedelta(seconds=rng.randint(-86_399, 86_399), microseconds=1))


def _seconds_to_parse(text: str) -> float:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        with pytest.raises(OffsetError):
            parse_offset(text)
        best = min(best, time.perf_counter() - start)
    return best


@pytest.mark.parametrize(
    "unit", ["9", "+", ":", " ", "+05:", "+0", LOOK_ALIKES[0], "-00:00:00", " +05:30 x"]
)
def test_hostile_input_takes_linear_time(unit: str) -> None:
    # A regular expression that backtracks would grow with the square of the length.
    small = _seconds_to_parse(unit * 50_000)
    large = _seconds_to_parse(unit * 400_000)
    assert large < 0.5
    assert large < max(small, 1e-4) * 40
