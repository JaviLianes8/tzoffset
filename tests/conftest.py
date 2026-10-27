"""Access to the fetched third-party sources, checked against their manifest."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

SOURCES = Path(__file__).resolve().parent / "vectors" / "sources"


def manifest(folder: Path = SOURCES) -> dict[str, tuple[str, int, str]]:
    """Map each file name of MANIFEST.txt to its (sha256, size, url)."""
    entries: dict[str, tuple[str, int, str]] = {}
    for line in (folder / "MANIFEST.txt").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            digest, size, name, url = line.split()
            entries[name] = (digest, int(size), url)
    return entries


def source_bytes(name: str, folder: Path = SOURCES) -> bytes:
    """Return a fetched file after checking its size and sha256 against the manifest.

    The files are not committed (python scripts/fetch_vectors.py fetches them): a test
    skips while one is absent and fails if one differs from the manifest.
    """
    path = folder / name
    if not path.is_file():
        pytest.skip(f"{name} not fetched; run python scripts/fetch_vectors.py")
    digest, size, _ = manifest(folder)[name]
    body = path.read_bytes()
    assert len(body) == size, f"{name} differs from MANIFEST.txt"
    assert hashlib.sha256(body).hexdigest() == digest, f"{name} differs from MANIFEST.txt"
    return body


_PAGE_BREAK = re.compile(r".*\[Page \d+\]\s*$|RFC \d+ {2,}.* {2,}\w+ \d{4}\s*$")


def source_text(name: str) -> str:
    """Return a fetched RFC as one line: page footers and headers dropped, every run of
    whitespace squashed to one space, so a sentence reads the same across a page break."""
    lines = source_bytes(name).decode("utf-8").splitlines()
    kept = [line for line in lines if not _PAGE_BREAK.fullmatch(line.strip("\x0c"))]
    return re.sub(r"\s+", " ", "\n".join(kept))
