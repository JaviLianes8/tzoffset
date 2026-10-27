"""Command line arguments: values after "--" and the cut of long usage messages."""

from __future__ import annotations

import pytest

from tzoffset._cli import _parser, main

PREFIX = "tzoffset: error: "


def _out(capsys: pytest.CaptureFixture[str], *argv: str) -> list[str]:
    assert main(list(argv)) == 0
    return capsys.readouterr().out.splitlines()


def _error_line(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as stop:
        main(list(argv))
    assert stop.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    line = captured.err.splitlines()[-1]
    assert line.startswith(PREFIX), line
    return line[len(PREFIX) :]


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--", "-05:30"], ["-05:30"]),
        (["--", "-08:00", "+01"], ["-08:00", "+01:00"]),
        (["--", "-05:30:15"], ["-05:30:15"]),
        (["-s", "compact", "--", "-05:30", "-0800"], ["-0530", "-0800"]),
        (["+01", "--", "-05:30"], ["+01:00", "-05:30"]),
    ],
)
def test_every_value_after_a_double_dash_is_an_offset(
    capsys: pytest.CaptureFixture[str], argv: list[str], expected: list[str]
) -> None:
    # Python 3.10 and 3.11 read "-05:30" after "--" as an unknown option unless shielded.
    assert _out(capsys, *argv) == expected


def test_an_option_name_after_a_double_dash_is_a_bad_offset(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _error_line(capsys, "+01", "--", "-s") == "not a valid lenient UTC offset: '-s'"


@pytest.mark.parametrize("size", [300, 5_000, 100_000])
def test_a_long_usage_message_is_cut_to_two_hundred_characters(
    capsys: pytest.CaptureFixture[str], size: int
) -> None:
    message = _error_line(capsys, "-s", "x" * size, "+01")
    assert len(message) == 200
    assert message.endswith("x" * 20 + "...")
    assert "argument -s/--style" in message


@pytest.mark.parametrize(("size", "cut"), [(199, False), (200, False), (201, True)])
def test_the_cut_starts_past_two_hundred_characters(
    capsys: pytest.CaptureFixture[str], size: int, cut: bool
) -> None:
    with pytest.raises(SystemExit):
        _parser().error("m" * size)
    line = capsys.readouterr().err.splitlines()[-1]
    expected = "m" * 197 + "..." if cut else "m" * size
    assert line == PREFIX + expected
