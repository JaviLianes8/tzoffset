"""Runnable public documentation and unchanged Literal semantics."""

from __future__ import annotations

import doctest
import os
import subprocess
import sys
from pathlib import Path

import pytest

import tzoffset


@pytest.mark.parametrize("name", tzoffset.__all__)
def test_every_public_name_has_a_runnable_docstring(name: str) -> None:
    doc = getattr(tzoffset, name).__doc__
    assert doc and ">>> " in doc, name
    test = doctest.DocTestParser().get_doctest(doc, {}, name, None, 0)
    assert test.examples, name
    result = doctest.DocTestRunner().run(test)
    assert result.failed == 0
    assert result.attempted == len(test.examples)


def test_documented_aliases_preserve_literal_semantics_without_shared_mutations() -> None:
    program = """
import pickle
import typing

shared = {
    'Grammar': typing.Literal['lenient', 'rfc3339', 'iso8601'],
    'Style': typing.Literal['colon', 'compact', 'short'],
    'Zero': typing.Literal['+', '-', 'Z'],
}
before = {name: vars(alias).copy() for name, alias in shared.items()}
import tzoffset
for name, original in shared.items():
    exported = getattr(tzoffset, name)
    assert vars(original) == before[name], name
    assert exported is not original, name
    assert exported == original and hash(exported) == hash(original), name
    assert type(exported) is type(original), name
    assert typing.get_origin(exported) is typing.Literal, name
    assert typing.get_args(exported) == typing.get_args(original), name
    assert repr(exported) == repr(original), name
    assert pickle.loads(pickle.dumps(exported)) == original, name
for function, parameter, name in (
    (tzoffset.parse_offset, 'grammar', 'Grammar'),
    (tzoffset.is_unknown_local_offset, 'grammar', 'Grammar'),
    (tzoffset.format_offset, 'style', 'Style'),
    (tzoffset.format_offset, 'zero', 'Zero'),
):
    assert typing.get_type_hints(function)[parameter] == shared[name], name
"""
    source = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env={**os.environ, "PYTHONPATH": str(source)},
    )
    assert result.returncode == 0, result.stdout + result.stderr
