"""The command line tool, driven in process and once as a real subprocess."""

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


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> list[str]:
    assert main(list(argv)) == 0
    return capsys.readouterr().out.splitlines()


def _fails(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as stop:
        main(list(argv))
    assert stop.value.code == 2
    return capsys.readouterr().err


def test_offsets_are_rewritten_in_order(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, "+0530", "-08", "Z", "-03:30") == ["+05:30", "-08:00", "+00:00", "-03:30"]


def test_options_may_follow_offsets(capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(capsys, "-08", "--style", "compact", "+01", "-z", "Z", "-00:00")
    assert out == ["-0800", "+0100", "Z"]


@pytest.mark.parametrize(
    ("flag", "value", "expected"),
    [("--style", "short", "+09"), ("-s", "compact", "+0900"), ("--style", "colon", "+09:00")],
)
def test_style_option(
    capsys: pytest.CaptureFixture[str], flag: str, value: str, expected: str
) -> None:
    assert _run(capsys, flag, value, "+09") == [expected]


@pytest.mark.parametrize(("value", "expected"), [("+", "+00:00"), ("-", "-00:00"), ("Z", "Z")])
def test_zero_option(capsys: pytest.CaptureFixture[str], value: str, expected: str) -> None:
    assert _run(capsys, "--zero", value, "+00:00") == [expected]


def test_double_dash_still_works(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(capsys, "-s", "short", "--", "-01", "+02") == ["-01", "+02"]


def test_grammar_option_is_applied(capsys: pytest.CaptureFixture[str]) -> None:
    assert "rfc3339" in _fails(capsys, "--grammar", "rfc3339", "+0530")
    assert "negative zero" in _fails(capsys, "-g", "iso8601", "-00:00")
    assert _run(capsys, "-g", "iso8601", "+0530") == ["+05:30"]


def test_bad_offset_exits_two_and_prints_nothing(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        main(["+01", "+25:00"])
    assert stop.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "+25:00" in captured.err


def test_offsets_or_zone_are_required(capsys: pytest.CaptureFixture[str]) -> None:
    assert "either OFFSET values or --zone" in _fails(capsys)


def test_offsets_and_zone_do_not_mix(capsys: pytest.CaptureFixture[str]) -> None:
    assert "either OFFSET values or --zone" in _fails(capsys, "--zone", "UTC", "+01")


def test_at_needs_zone(capsys: pytest.CaptureFixture[str]) -> None:
    assert "--at needs --zone" in _fails(capsys, "+01", "--at", "2026-01-01T00:00")


def _need_zones() -> None:
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        zoneinfo.ZoneInfo("America/New_York")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no time zone database")


def test_zone_at_a_naive_moment_is_wall_time(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    zone = ["--zone", "America/New_York"]
    assert _run(capsys, *zone, "--at", "2026-03-08T01:59") == ["-05:00"]
    assert _run(capsys, *zone, "--at", "2026-03-08T03:00", "-s", "short") == ["-04"]


def test_zone_at_an_aware_moment_is_converted(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    # 06:59 UTC is 01:59 EST, a minute before the 2026 spring change; 07:00 UTC is 03:00 EDT.
    zone = ["--zone", "America/New_York"]
    assert _run(capsys, *zone, "--at", "2026-03-08T06:59+00:00") == ["-05:00"]
    assert _run(capsys, *zone, "--at", "2026-03-08T07:00Z") == ["-04:00"]
    # Noon in Tokyo is 22:00 the evening before in New York, still on standard time.
    assert _run(capsys, *zone, "--at", "2026-03-08T12:00+09:00") == ["-05:00"]


def test_zone_without_at_uses_now(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    assert _run(capsys, "--zone", "UTC", "--zero", "Z") == ["Z"]


def test_unknown_zone_and_bad_moment_exit_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert "unknown time zone" in _fails(capsys, "--zone", "Mars/Olympus")
    assert "unknown time zone" in _fails(capsys, "--zone", "../etc")
    _need_zones()
    assert "not an ISO 8601" in _fails(capsys, "--zone", "UTC", "--at", "noon")


def test_module_runs_and_reports_its_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tzoffset", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stderr
    from tzoffset import __version__

    assert result.stdout.strip() == f"tzoffset {__version__}"


class _Pipe(io.StringIO):
    def __init__(self, error: OSError) -> None:
        super().__init__()
        self.error = error

    def write(self, text: str) -> int:
        raise self.error

    def fileno(self) -> int:
        return sys.__stdout__.fileno() if sys.__stdout__ else 1


@pytest.mark.parametrize("error", [BrokenPipeError(), OSError(errno.EINVAL, "closed")])
def test_a_closed_pipe_ends_quietly(monkeypatch: pytest.MonkeyPatch, error: OSError) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(sys, "stdout", _Pipe(error))
    monkeypatch.setattr(os, "dup2", lambda a, b: calls.append((a, b)))
    assert main(["+01", "+02"]) == 0
    assert len(calls) == 1


def test_other_write_errors_are_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", _Pipe(OSError(errno.ENOSPC, "disk full")))
    with pytest.raises(OSError, match="disk full"):
        main(["+01"])
