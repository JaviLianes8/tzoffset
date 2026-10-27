"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with TZOFFSET_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("TZOFFSET_E2E") != "1", reason="set TZOFFSET_E2E=1 to build"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources
from datetime import datetime, timedelta, timezone
import tzoffset as t

assert "site-packages" in t.__file__, t.__file__
assert importlib.metadata.version("tzoffset") == t.__version__
assert importlib.resources.files("tzoffset").joinpath("py.typed").is_file()
assert sorted(t.__all__) == sorted([
    "Grammar", "OffsetError", "Style", "Zero",
    "format_offset", "is_unknown_local_offset", "parse_offset"])

assert t.parse_offset("+05:30") == timezone(timedelta(hours=5, minutes=30))
assert t.parse_offset("-0800", grammar="iso8601") == timezone(timedelta(hours=-8))
assert t.parse_offset("Z", grammar="rfc3339") is timezone.utc
assert t.is_unknown_local_offset("-00:00") and not t.is_unknown_local_offset("+00:00")
assert t.format_offset(timedelta(hours=9), style="short") == "+09"
assert t.format_offset(timezone.utc, zero="Z") == "Z"
assert t.format_offset(datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=-3)))) == "-03:00"
for bad, grammar in (("+0530", "rfc3339"), ("-00:00", "iso8601"), ("+24:00", "lenient")):
    try:
        t.parse_offset(bad, grammar=grammar)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
try:
    t.parse_offset(None)
except TypeError:
    pass
else:
    raise AssertionError("None")
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> bytes:
    result = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    (wheel,) = dist.glob("tzoffset-*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert not [name for name in names if "vectors" in name or name.startswith("tests/")]
    assert {"tzoffset/py.typed", "tzoffset/__main__.py", "tzoffset/_cli.py"} <= set(names)

    _run(sys.executable, "-m", "build", "--sdist", "--outdir", dist, ROOT)
    (sdist,) = dist.glob("tzoffset-*.tar.gz")
    with tarfile.open(sdist) as archive:
        members = archive.getnames()
    # Third-party sources stay out; only their manifest and the recorded Java output ship.
    data = sorted(name.split("/tests/vectors/")[1] for name in members if "/tests/vectors/" in name)
    assert data == ["java/zoneoffset.txt", "sources/MANIFEST.txt"]
    assert not [name for name in members if "CERT-1.0" in name or "IMPROVEMENTS" in name]

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    _run(python, "-m", "pip", "install", "-q", wheel)

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    assert _run(python, "-I", "-c", PROGRAM, cwd=work).decode().splitlines() == ["e2e ok"]

    script = bindir / ("tzoffset.exe" if sys.platform == "win32" else "tzoffset")
    out = _run(script, "+0530", "-08", "-s", "compact", "--zero", "Z", "+00:00", cwd=work)
    assert out.decode().split() == ["+0530", "-0800", "Z"]
    out = _run(python, "-I", "-m", "tzoffset", "-g", "iso8601", "-0530", cwd=work)
    assert out.decode().split() == ["-05:30"]
    bad = subprocess.run([str(script), "+25:00"], cwd=work, capture_output=True, check=False)
    assert bad.returncode == 2
    assert b"offset field out of range" in bad.stderr
