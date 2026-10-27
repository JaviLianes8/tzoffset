"""Exit status and output of the command line tool: version, closed pipes, write errors."""

from __future__ import annotations

import errno
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tzoffset._cli import main

SRC = Path(__file__).resolve().parents[1] / "src"
ENV = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"}


def test_module_runs_and_reports_its_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tzoffset", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    from tzoffset import __version__

    assert result.stdout.strip() == f"tzoffset {__version__}"


@pytest.mark.parametrize("argv", [["+01", "-08"], ["--help"], ["--version"]])
def test_a_reader_that_leaves_first_gets_status_one_and_no_noise(argv: list[str]) -> None:
    process = subprocess.Popen(
        [sys.executable, "-m", "tzoffset", *argv],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=ENV,
    )
    assert process.stdout is not None and process.stderr is not None
    process.stdout.close()  # gone before the interpreter has even started
    err = process.stderr.read()
    assert process.wait(timeout=60) == 1
    assert err == b""


class _Pipe(io.StringIO):
    def __init__(self, error: OSError) -> None:
        super().__init__()
        self.error = error

    def write(self, text: str) -> int:
        raise self.error

    def fileno(self) -> int:
        return sys.__stdout__.fileno() if sys.__stdout__ else 1


@pytest.mark.parametrize("error", [BrokenPipeError(), OSError(errno.EINVAL, "closed")])
def test_a_closed_pipe_ends_quietly_with_status_one(
    monkeypatch: pytest.MonkeyPatch, error: OSError
) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(sys, "stdout", _Pipe(error))
    monkeypatch.setattr(os, "dup2", lambda a, b: calls.append((a, b)))
    assert main(["+01", "+02"]) == 1
    assert len(calls) == 1


@pytest.mark.parametrize("flag", ["--help", "--version"])
def test_lost_help_or_version_is_status_one(monkeypatch: pytest.MonkeyPatch, flag: str) -> None:
    monkeypatch.setattr(sys, "stdout", _Pipe(BrokenPipeError()))
    monkeypatch.setattr(os, "dup2", lambda a, b: None)
    with pytest.raises(SystemExit) as stop:
        main([flag])
    assert stop.value.code == 1


def test_other_write_errors_are_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", _Pipe(OSError(errno.ENOSPC, "disk full")))
    with pytest.raises(OSError, match="disk full"):
        main(["+01"])


def test_a_write_error_while_parsing_is_handled_like_one_while_printing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Python 3.10's argparse lets the write error of --help and --version escape.
    import tzoffset._cli as cli

    def lost(parser: object, argv: object) -> list[str]:
        raise BrokenPipeError

    monkeypatch.setattr(cli, "_lines", lost)
    monkeypatch.setattr(os, "dup2", lambda a, b: None)
    with pytest.raises(SystemExit) as stop:
        main(["--help"])
    assert stop.value.code == 1

    def full(parser: object, argv: object) -> list[str]:
        raise OSError(errno.ENOSPC, "disk full")

    monkeypatch.setattr(cli, "_lines", full)
    with pytest.raises(OSError, match="disk full"):
        main(["--help"])
