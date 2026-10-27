"""Literal aliases for the options of the public functions.

``Grammar`` names the spellings ``parse_offset`` accepts, ``Style`` how ``format_offset``
writes hours, minutes and seconds, and ``Zero`` how it writes a zero offset. typing caches
``Literal[...]`` objects and shares them with every other alias of the same values, so the
aliases carry no ``__doc__`` of their own: their documentation lives here, in the GUIDE and
in the examples of ``__test__`` below.
"""

from __future__ import annotations

from typing import Literal

#: Which spellings ``parse_offset`` accepts: ``"lenient"`` (the default), ``"rfc3339"``
#: (RFC 3339 section 5.6) or ``"iso8601"`` (RFC 3339 Appendix A, RFC 9557 section 2).
Grammar = Literal["lenient", "rfc3339", "iso8601"]

#: How ``format_offset`` writes hours, minutes and seconds: ``"colon"`` (``+05:30``),
#: ``"compact"`` (``+0530``) or ``"short"`` (``+05`` when minutes and seconds are zero).
Style = Literal["colon", "compact", "short"]

#: How ``format_offset`` writes a zero offset: ``"+"`` (``+00:00``), ``"-"`` (``-00:00``)
#: or ``"Z"``.
Zero = Literal["+", "-", "Z"]

GRAMMARS: tuple[Grammar, ...] = ("lenient", "rfc3339", "iso8601")
STYLES: tuple[Style, ...] = ("colon", "compact", "short")
ZEROS: tuple[Zero, ...] = ("+", "-", "Z")

# doctest only looks at functions, classes and modules; the alias examples run from here.
__test__ = {
    "Grammar": """Which spellings ``parse_offset`` accepts.

``"lenient"`` (the default) takes ``Z``, ``+hh``, ``+hhmm``, ``+hh:mm``, ``+hhmmss``,
``+hh:mm:ss`` and surrounding ASCII whitespace; ``"rfc3339"`` takes only ``Z`` and
``+hh:mm``; ``"iso8601"`` takes ``Z``, ``+hh``, ``+hhmm`` and ``+hh:mm`` without a
negative zero.

>>> import typing
>>> from tzoffset import Grammar, parse_offset
>>> typing.get_args(Grammar)
('lenient', 'rfc3339', 'iso8601')
>>> parse_offset("+0530", grammar="iso8601")
datetime.timezone(datetime.timedelta(seconds=19800))
""",
    "Style": """How ``format_offset`` writes hours, minutes and seconds.

>>> import typing
>>> from datetime import timedelta
>>> from tzoffset import Style, format_offset
>>> typing.get_args(Style)
('colon', 'compact', 'short')
>>> [format_offset(timedelta(hours=9), style=style) for style in typing.get_args(Style)]
['+09:00', '+0900', '+09']
""",
    "Zero": """How ``format_offset`` writes a zero offset.

>>> import typing
>>> from datetime import timedelta
>>> from tzoffset import Zero, format_offset
>>> typing.get_args(Zero)
('+', '-', 'Z')
>>> [format_offset(timedelta(0), zero=zero) for zero in typing.get_args(Zero)]
['+00:00', '-00:00', 'Z']
""",
}
