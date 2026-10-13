"""Literal aliases for the options of the public functions."""

from __future__ import annotations

from typing import Literal

Grammar = Literal["lenient", "rfc3339", "iso8601"]
"""Which spellings ``parse_offset`` accepts."""

Style = Literal["colon", "compact", "short"]
"""How ``format_offset`` writes hours, minutes and seconds."""

Zero = Literal["+", "-", "Z"]
"""How ``format_offset`` writes a zero offset: ``+00:00``, ``-00:00`` or ``Z``."""

GRAMMARS: tuple[Grammar, ...] = ("lenient", "rfc3339", "iso8601")
STYLES: tuple[Style, ...] = ("colon", "compact", "short")
ZEROS: tuple[Zero, ...] = ("+", "-", "Z")
