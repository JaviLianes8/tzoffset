"""The public API is typed: mypy infers results and rejects bad calls."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

SRC = Path(__file__).resolve().parents[1] / "src"

SNIPPET = """
import datetime as dt
import tzoffset as t
reveal_type(t.parse_offset("+05:30"))
reveal_type(t.format_offset(dt.timedelta(hours=1)))
reveal_type(t.is_unknown_local_offset("Z"))
t.parse_offset(b"+05:30")
t.parse_offset("+05:30", grammar="rfc2822")
t.format_offset(dt.timedelta(0), style="iso")
t.format_offset(dt.timedelta(0), zero="z")
t.format_offset(3600)
t.parse_offset("+05:30", "rfc3339")
g: t.Grammar = "iso8601"
s: t.Style = "short"
z: t.Zero = "Z"
t.format_offset(dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc), style=s, zero=z)
t.format_offset(dt.timezone.utc)
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    )
    return str(out) + str(err)


@pytest.mark.parametrize(
    ("line", "expected"),
    [(4, r"datetime\.timezone"), (5, r"(builtins\.)?str"), (6, r"(builtins\.)?bool")],
)
def test_results_are_typed(mypy_output: str, line: int, expected: str) -> None:
    assert re.search(rf'snippet\.py:{line}: note: Revealed type is "{expected}"', mypy_output), (
        mypy_output
    )


@pytest.mark.parametrize(
    ("line", "code"),
    [(7, "arg-type"), (8, "arg-type"), (9, "arg-type"), (10, "arg-type"), (11, "arg-type")],
)
def test_wrong_calls_are_rejected(mypy_output: str, line: int, code: str) -> None:
    assert re.search(rf"snippet\.py:{line}: error: .*\[{code}\]", mypy_output), mypy_output


def test_grammar_is_keyword_only(mypy_output: str) -> None:
    assert re.search(r"snippet\.py:12: error: Too many positional", mypy_output), mypy_output


def test_the_aliases_and_good_calls_pass(mypy_output: str) -> None:
    for line in range(13, 18):
        assert not re.search(rf"snippet\.py:{line}: error", mypy_output), mypy_output
