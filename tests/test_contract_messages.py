"""Fabricated credential canaries must never appear in API or CLI diagnostics."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
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

CANARY = "R4nd0mCredential9988"
SECRET = "secret=" + CANARY
CALLS: list[Callable[[str], object]] = [
    parse_offset,
    is_unknown_local_offset,
    lambda v: parse_offset("Z", grammar=cast(Grammar, v)),
    lambda v: is_unknown_local_offset("Z", grammar=cast(Grammar, v)),
    lambda v: format_offset(timedelta(0), style=cast(Style, v)),
    lambda v: format_offset(timedelta(0), zero=cast(Zero, v)),
]


@pytest.mark.parametrize("call", CALLS)
@pytest.mark.parametrize("suffix", ["", "x" * 1000])
def test_api_diagnostics_do_not_echo_text(call: Callable[[str], object], suffix: str) -> None:
    with pytest.raises(OffsetError) as caught:
        call(SECRET + suffix)
    message = str(caught.value)
    assert CANARY not in message and "secret=" not in message
    assert len(message) < 200


@pytest.mark.parametrize(
    "argv",
    [
        [SECRET],
        ["--style", SECRET, "Z"],
        ["--zero=" + SECRET, "Z"],
        ["--grammar", SECRET, "Z"],
        ["--zone", SECRET],
        ["--zone", "UTC", "--at", SECRET],
        ["Z", "--" + SECRET],
        ["Z", "--st" + SECRET],
        ["--help=" + SECRET],
        ["--version=" + SECRET],
        ["--z=" + SECRET],
        ["-s" + SECRET, "Z"],
    ],
)
def test_cli_diagnostics_do_not_echo_arguments(argv: list[str]) -> None:
    source = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [sys.executable, "-m", "tzoffset", *argv],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env={**os.environ, "PYTHONPATH": str(source)},
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert CANARY not in result.stderr and "secret=" not in result.stderr
    assert "Traceback" not in result.stderr
    assert len(result.stderr) < 1000


@pytest.mark.parametrize(
    ("zone", "at"),
    [
        ("Etc/GMT+12", "0001-01-01T00:00:00.8642091357Z"),
        ("Etc/GMT-14", "9999-12-31T23:59:59.8642091357Z"),
    ],
)
def test_cli_calendar_overflow_diagnostics_omit_both_arguments(zone: str, at: str) -> None:
    source = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [sys.executable, "-m", "tzoffset", "--zone", zone, "--at", at],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env={**os.environ, "PYTHONPATH": str(source)},
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert zone not in result.stderr and at not in result.stderr
    assert "8642091357" not in result.stderr
    assert result.stderr.splitlines()[-1] == (
        "tzoffset: error: --at is out of range in the selected time zone"
    )
    assert "Traceback" not in result.stderr
    assert len(result.stderr) < 1000
