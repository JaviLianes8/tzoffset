"""Run the command line tool with ``python -m tzoffset``."""

from __future__ import annotations

import sys

from tzoffset._cli import main

if __name__ == "__main__":
    sys.exit(main())
