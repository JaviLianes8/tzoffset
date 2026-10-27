"""Argument checks shared by the public functions, with messages of bounded size."""

from __future__ import annotations

from typing import TypeVar

from ._errors import OffsetError

# A message quotes at most this many characters of what the caller passed, so a huge or
# hostile argument never turns into a huge message.
QUOTE_LIMIT = 40

_Option = TypeVar("_Option", bound=str)


def quote(text: str) -> str:
    """Return ``repr(text)``, cut to its first characters when it is long."""
    if len(text) <= QUOTE_LIMIT:
        return repr(text)
    return f"{text[:QUOTE_LIMIT]!r}... ({len(text)} characters)"


def kind(value: object) -> str:
    """Return the type name of ``value`` for a message, cut when it is long."""
    name = type(value).__name__
    return name if len(name) <= QUOTE_LIMIT else name[:QUOTE_LIMIT] + "..."


def plain(value: object, name: str) -> str:
    """Return ``value`` as an exact ``str``; anything that is not a ``str`` is a ``TypeError``."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str, not {kind(value)}")
    # A str subclass may override strip, __eq__ or __repr__; only its characters are used.
    return str.__str__(value)


def choice(value: object, name: str, options: tuple[_Option, ...]) -> _Option:
    """Return the option equal to ``value``; ``TypeError`` or ``OffsetError`` otherwise."""
    text = plain(value, name)
    for option in options:
        if text == option:
            return option
    expected = ", ".join(repr(option) for option in options)
    raise OffsetError(f"unknown {name}: {quote(text)} (expected one of {expected})")
