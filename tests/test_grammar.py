"""What each named grammar accepts and rejects."""

from __future__ import annotations

from datetime import timedelta, timezone

import pytest

from tzoffset import Grammar, OffsetError, is_unknown_local_offset, parse_offset

H = timedelta(hours=1)
M = timedelta(minutes=1)

# text, offset it means, and whether lenient, rfc3339 and iso8601 accept it
CASES: list[tuple[str, timedelta, bool, bool, bool]] = [
    ("Z", timedelta(0), True, True, True),
    ("z", timedelta(0), True, True, True),
    ("+05:30", 5 * H + 30 * M, True, True, True),
    ("-23:59", -(23 * H + 59 * M), True, True, True),
    ("+0530", 5 * H + 30 * M, True, False, True),
    ("+05", 5 * H, True, False, True),
    ("-12", -12 * H, True, False, True),
    ("+14:00", 14 * H, True, True, True),
    ("+05:30:45", 5 * H + 30 * M + timedelta(seconds=45), True, False, False),
    ("+053045", 5 * H + 30 * M + timedelta(seconds=45), True, False, False),
    ("+00:00", timedelta(0), True, True, True),
    ("-00:00", timedelta(0), True, True, False),
    ("-0000", timedelta(0), True, False, False),
    ("-00", timedelta(0), True, False, False),
    (" +05:30 ", 5 * H + 30 * M, True, False, False),
    ("+05:30\n", 5 * H + 30 * M, True, False, False),
]
GRAMMARS: list[Grammar] = ["lenient", "rfc3339", "iso8601"]


@pytest.mark.parametrize(("text", "offset", "lenient", "rfc", "iso"), CASES)
def test_each_grammar_accepts_exactly_its_forms(
    text: str, offset: timedelta, lenient: bool, rfc: bool, iso: bool
) -> None:
    for grammar, accepted in zip(GRAMMARS, (lenient, rfc, iso), strict=True):
        if accepted:
            assert parse_offset(text, grammar=grammar) == timezone(offset), grammar
        else:
            with pytest.raises(OffsetError):
                parse_offset(text, grammar=grammar)


@pytest.mark.parametrize("grammar", GRAMMARS)
@pytest.mark.parametrize(
    "text",
    [
        "",
        "+",
        "+5",
        "05:30",
        "+24:00",
        "+24",
        "+2400",
        "+99:00",
        "+05:60",
        "+0560",
        "+05:30:60",
        "+05-30",
        "++05",
        "+05:3045",
        "+0530:45",
        "+5:30",
        "+05:3",
        "+05:30:4",
        "UTC",
        "GMT+1",
        "Zz",
        "+\u0660\u0665:\u0663\u0660",
        "+\uff10\uff15:30",
        "+05:\u0663\u0660",
        "+05\u0663\u0660",
        "+05:30:\u0664\u0665",
        "+0530\u0664\u0665",
        "\u221205:00",
    ],
)
def test_every_grammar_rejects(grammar: Grammar, text: str) -> None:
    with pytest.raises(OffsetError):
        parse_offset(text, grammar=grammar)


def test_error_names_the_grammar_and_the_text() -> None:
    with pytest.raises(OffsetError, match=r"rfc3339 .*'\+0530'"):
        parse_offset("+0530", grammar="rfc3339")


def test_iso8601_explains_the_negative_zero() -> None:
    with pytest.raises(OffsetError, match="negative zero"):
        parse_offset("-00:00", grammar="iso8601")


def test_unknown_grammar_is_rejected() -> None:
    with pytest.raises(OffsetError, match="unknown grammar"):
        parse_offset("+05:00", grammar="rfc2822")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("text", "unknown"),
    [
        ("Z", True),
        ("z", True),
        ("-00:00", True),
        ("-0000", True),
        ("-00", True),
        ("-00:00:00", True),
        ("+00:00", False),
        ("+00", False),
        ("-00:00:01", False),
        ("-00:01", False),
        ("+05:30", False),
    ],
)
def test_unknown_local_offset(text: str, unknown: bool) -> None:
    assert is_unknown_local_offset(text) is unknown


def test_unknown_local_offset_follows_the_grammar() -> None:
    assert is_unknown_local_offset("-00:00", grammar="rfc3339") is True
    with pytest.raises(OffsetError):
        is_unknown_local_offset("-0000", grammar="rfc3339")
    with pytest.raises(OffsetError):
        is_unknown_local_offset("-00:00", grammar="iso8601")


def test_unknown_local_offset_validates_the_text() -> None:
    with pytest.raises(OffsetError):
        is_unknown_local_offset("-00:60")
    with pytest.raises(TypeError):
        is_unknown_local_offset(None)  # type: ignore[arg-type]
