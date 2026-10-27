"""Regenerate tests/vectors/java/zoneoffset.txt from java.time.ZoneOffset.

Needs a JDK 11 or later on PATH (``java`` runs the single source file directly). The output
is committed so the tests run without Java; this script records the Java version used.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "oracle" / "ZoneOffsetOracle.java"
OUTPUT = ROOT / "tests" / "vectors" / "java" / "zoneoffset.txt"
ODD = ["Z", "z", "+5", "-9", "+05:3", "+5:30", "+05:30:4", "+0530:45", "+05:3045", " +05:30"]
ODD += ["+05:30 ", "", "+", "-", "05:30", "+-05:30", "++05", "+05.5", "UTC"]


def inputs() -> list[str]:
    """Every sign and hour 00-25 with boundary minutes and seconds, in both spellings."""
    texts = list(ODD)
    for sign in "+-":
        for hour in range(26):
            head = f"{sign}{hour:02d}"
            texts.append(head)
            for sep in ("", ":"):
                texts += [f"{head}{sep}{minute:02d}" for minute in (0, 1, 30, 45, 59, 60)]
                for minute in (0, 30, 59):
                    texts += [f"{head}{sep}{minute:02d}{sep}{s:02d}" for s in (0, 1, 59, 60)]
    lines = [f"P {text}" for text in texts]
    seconds = sorted(set(range(-64800, 64801, 60)) | set(range(-64800, 64801, 97)))
    return lines + [f"F {value}" for value in seconds]


def main() -> int:
    version = subprocess.run(
        ["java", "-version"], capture_output=True, text=True, check=True
    ).stderr.splitlines()
    result = subprocess.run(
        ["java", str(SOURCE)],
        input="".join(line + "\n" for line in inputs()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    header = [
        "# Output of scripts/oracle/ZoneOffsetOracle.java (java.time.ZoneOffset), written by",
        "# python scripts/java_oracle.py. Real program output, not hand-written.",
        f"# Generated: {datetime.date.today().isoformat()}",
        *(f"# {line}" for line in version),
        "# P <text><TAB><total seconds or ERR>",
        "# F <seconds><TAB><id> <pattern xxxxx> <pattern xxxx> <appendOffset +HH:mm:ss, +00>",
    ]
    OUTPUT.write_text("\n".join(header) + "\n" + result.stdout, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.relative_to(ROOT)}: {len(result.stdout.splitlines())} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
