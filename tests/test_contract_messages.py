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
