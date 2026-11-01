"""Upgrade the actual PyPI 0.2.0 release in place and compare its stable public behaviour."""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("TZOFFSET_E2E_PYPI") != "1", reason="set TZOFFSET_E2E_PYPI=1 for PyPI"
)

ROOT = Path(__file__).resolve().parents[1]

# Expected values come from the installed PyPI release, run before and after the upgrade.
PROGRAM = r"""
import hashlib, importlib.metadata, inspect, json, random, sys, typing
from datetime import datetime, timedelta, timezone
import tzoffset as t

assert "site-packages" in t.__file__, t.__file__
assert t.__version__ == importlib.metadata.version("tzoffset") == sys.argv[1]
results = [sorted(t.__all__)]
for name in ("parse_offset", "format_offset", "is_unknown_local_offset"):
    results.append(str(inspect.signature(getattr(t, name))))
for alias in (t.Grammar, t.Style, t.Zero):
    results.append(typing.get_args(alias))
rng = random.Random(20261101)
seconds = list(range(-86340, 86341, 60)) + [-86399, 86399, -1, 0, 1]
seconds += [rng.randrange(-86399, 86400) for _ in range(4000)]
for n in seconds:
    delta = timedelta(seconds=n)
    zone = timezone(delta)
    moment = datetime(2026, 1, 1, tzinfo=zone)
    for style in typing.get_args(t.Style):
        for zero in typing.get_args(t.Zero):
            text = t.format_offset(delta, style=style, zero=zero)
            assert text == t.format_offset(zone, style=style, zero=zero)
            assert text == t.format_offset(moment, style=style, zero=zero)
            results.append(text)
            for grammar in typing.get_args(t.Grammar):
                try:
                    parsed = t.parse_offset(text, grammar=grammar)
                    unknown = t.is_unknown_local_offset(text, grammar=grammar)
                except t.OffsetError:
                    results.append(None)
                else:
                    assert type(parsed) is timezone
                    assert parsed.utcoffset(None) == delta
                    assert n or parsed is timezone.utc
                    results.append((n, unknown))
alphabet = "0123456789+-:Zz \t\n\r\v\f\u00a0\u0660\uff11abc"
texts = ["Z", "z", "-00", "-0000", "-00:00", "-000000", "-00:00:00", " +05:30 "]
texts += ["".join(rng.choices(alphabet, k=rng.randrange(24))) for _ in range(6000)]
for text in texts:
    for grammar in typing.get_args(t.Grammar):
        try:
            offset = t.parse_offset(text, grammar=grammar).utcoffset(None)
            unknown = t.is_unknown_local_offset(text, grammar=grammar)
        except t.OffsetError:
            results.append(None)
        else:
            results.append((int(offset.total_seconds()), unknown))
print(hashlib.sha256(json.dumps(results).encode()).hexdigest())
"""


def _run(*cmd: str | Path, cwd: Path) -> bytes:
    result = subprocess.run(
        [str(part) for part in cmd], cwd=cwd, capture_output=True, check=False, timeout=180
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def test_pypi_release_upgrades_in_place_without_changing_the_stable_api(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT, cwd=tmp_path)
    (wheel,) = dist.glob("tzoffset-1.0.0-*.whl")
    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    work = tmp_path / "consumer"
    work.mkdir()
    _run(
        python,
        "-m",
        "pip",
        "install",
        "--index-url",
        "https://pypi.org/simple",
        "--only-binary=:all:",
        "tzoffset==0.2.0",
        cwd=work,
    )
    before = _run(python, "-I", "-c", PROGRAM, "0.2.0", cwd=work)
    command = bindir / ("tzoffset.exe" if sys.platform == "win32" else "tzoffset")
    cli_before = _run(command, "+0530", "-08", "Z", "-s", "compact", cwd=work)
    assert cli_before.decode().splitlines() == ["+0530", "-0800", "+0000"]
    _run(python, "-m", "pip", "install", "--upgrade", "--no-deps", wheel, cwd=work)
    assert _run(python, "-I", "-c", PROGRAM, "1.0.0", cwd=work) == before
    assert _run(command, "+0530", "-08", "Z", "-s", "compact", cwd=work) == cli_before
    assert _run(python, "-I", "-m", "tzoffset", "--version", cwd=work).strip() == b"tzoffset 1.0.0"
