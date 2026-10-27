"""Literal aliases for the options of the public functions."""

from __future__ import annotations

from typing import Literal

Grammar = Literal["lenient", "rfc3339", "iso8601"]
Grammar.__doc__ = """Which spellings ``parse_offset`` accepts.

``"lenient"`` (the default) takes ``Z``, ``+hh``, ``+hhmm``, ``+hh:mm``, ``+hhmmss``,
``+hh:mm:ss`` and surrounding ASCII whitespace; ``"rfc3339"`` takes only ``Z`` and
``+hh:mm`` (RFC 3339 section 5.6); ``"iso8601"`` takes ``Z``, ``+hh``, ``+hhmm`` and
``+hh:mm`` without a negative zero (RFC 3339 Appendix A, RFC 9557 section 2).

>>> import typing
>>> from tzoffset import Grammar
>>> typing.get_args(Grammar)
('lenient', 'rfc3339', 'iso8601')
"""

Style = Literal["colon", "compact", "short"]
Style.__doc__ = """How ``format_offset`` writes hours, minutes and seconds.

``"colon"`` writes ``+05:30``, ``"compact"`` writes ``+0530`` and ``"short"`` writes
``+05`` when minutes and seconds are zero, otherwise the colon form. A seconds field is
added only when the seconds are not zero.

>>> import typing
>>> from tzoffset import Style
>>> typing.get_args(Style)
('colon', 'compact', 'short')
"""

Zero = Literal["+", "-", "Z"]
Zero.__doc__ = """How ``format_offset`` writes a zero offset: ``+00:00``, ``-00:00`` or ``Z``.

>>> import typing
>>> from tzoffset import Zero
>>> typing.get_args(Zero)
('+', '-', 'Z')
"""

GRAMMARS: tuple[Grammar, ...] = ("lenient", "rfc3339", "iso8601")
STYLES: tuple[Style, ...] = ("colon", "compact", "short")
ZEROS: tuple[Zero, ...] = ("+", "-", "Z")

# doctest only looks at functions, classes and modules; the alias examples run from here.
__test__ = {"Grammar": Grammar.__doc__, "Style": Style.__doc__, "Zero": Zero.__doc__}
