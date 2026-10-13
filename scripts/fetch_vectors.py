"""Fetch the third-party sources listed in tests/vectors/sources/MANIFEST.txt.

The files are third-party and are not committed. Each download is checked against the size
and SHA-256 in the manifest; a mismatch aborts without keeping the file.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

FOLDER = Path(__file__).resolve().parents[1] / "tests" / "vectors" / "sources"


def main() -> int:
    for line in (FOLDER / "MANIFEST.txt").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        digest, size, name, url = line.split()
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if len(data) != int(size) or hashlib.sha256(data).hexdigest() != digest:
            print(f"{name}: size or sha256 does not match the manifest", file=sys.stderr)
            return 1
        (FOLDER / name).write_bytes(data)
        print(f"{name}: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
