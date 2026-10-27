"""The README examples run and print what they say; metadata agrees with the code."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

import tzoffset
from tzoffset._cli import main

ROOT = Path(__file__).resolve().parents[1]


def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def _blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", _readme(), flags=re.DOTALL)


def _expected(block: str) -> list[str]:
    # A run of comment lines right under code is the output of the code above it.
    results: list[str] = []
    open_run = False
    for line in block.splitlines():
        if line.startswith("# ") and open_run:
            results.append(line[2:])
        else:
            open_run = bool(line) and not line.startswith("#")
    return results


def _need_zones(text: str) -> None:
    zoneinfo = pytest.importorskip("zoneinfo")
    names = re.findall(r'ZoneInfo\("([^"]+)"\)|--zone (\S+)', text)
    assert names
    for name in ["".join(pair) for pair in names]:
        try:
            zoneinfo.ZoneInfo(name)
        except zoneinfo.ZoneInfoNotFoundError:
            pytest.skip(f"no time zone database with {name}")


def test_the_readme_has_its_four_examples() -> None:
    assert len(_blocks()) == 4


def _guide_blocks() -> list[str]:
    text = (ROOT / "GUIDE.md").read_text(encoding="utf-8")
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


@pytest.mark.parametrize("index", range(3))
def test_each_guide_example_prints_what_its_comments_say(
    index: int, capsys: pytest.CaptureFixture[str]
) -> None:
    assert len(_guide_blocks()) == 3
    block = _guide_blocks()[index]
    exec(compile(block, "GUIDE.md", "exec"), {"__name__": "guide"})
    printed = capsys.readouterr().out.splitlines()
    assert printed == _expected(block)
    assert len(printed) >= 2


def test_the_readme_links_are_absolute() -> None:
    links = re.findall(r"\]\(([^)]+)\)", _readme())
    assert len(links) >= 4
    assert all(link.startswith("https://") for link in links), links


@pytest.mark.parametrize("index", range(4))
def test_each_example_prints_what_its_comments_say(
    index: int, capsys: pytest.CaptureFixture[str]
) -> None:
    block = _blocks()[index]
    if "ZoneInfo" in block:
        _need_zones(block)
    exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
    printed = capsys.readouterr().out.splitlines()
    assert printed == _expected(block)
    assert len(printed) >= 3


def test_the_command_line_examples_match_the_tool(capsys: pytest.CaptureFixture[str]) -> None:
    session = re.search(r"```\n(\$ tzoffset .*?)```", _readme(), flags=re.DOTALL)
    assert session is not None
    _need_zones(session.group(1))
    transcript: list[str] = []
    for line in session.group(1).splitlines():
        if line.startswith("$ tzoffset "):
            assert main(shlex.split(line[len("$ tzoffset ") :])) == 0
            transcript += [line, *capsys.readouterr().out.splitlines()]
    assert transcript == session.group(1).splitlines()
    assert len(transcript) == 9


def test_every_public_name_appears_in_the_readme() -> None:
    for name in tzoffset.__all__:
        if name not in ("Grammar", "Style", "Zero"):
            assert f"`{name}" in _readme(), name


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == tzoffset.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{tzoffset.__version__}]" in text


def _code() -> list[Path]:
    paths = [*ROOT.glob("src/**/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("scripts/**/*")]
    return [path for path in paths if path.is_file()]


def _shipped() -> list[Path]:
    vectors = ROOT / "tests" / "vectors"
    return [
        *ROOT.glob("*.md"),
        *ROOT.glob("*.toml"),
        *_code(),
        vectors / "sources" / "MANIFEST.txt",
        vectors / "java" / "zoneoffset.txt",
    ]


def test_no_em_dash_in_any_shipped_text() -> None:
    for path in _shipped():
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_every_source_file_stays_under_two_hundred_lines() -> None:
    assert len(_code()) > 20
    for path in _code():
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path


def test_sources_are_ascii() -> None:
    # The docs may quote a Unicode look-alike; code and data spell them as escapes.
    for path in [path for path in _shipped() if path.suffix != ".md"]:
        assert path.read_text(encoding="utf-8").isascii(), path
