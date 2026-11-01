"""Argument checks shared by the public functions, with messages of bounded size."""

from __future__ import annotations

from typing import TypeVar

from ._errors import OffsetError

_NAME_LIMIT = 40
_TYPE_NAME = vars(type)["__name__"]

_Option = TypeVar("_Option", bound=str)


def kind(value: object) -> str:
    """Return a bounded, escaped stored type name without metaclass callbacks."""
    name = str.__str__(_TYPE_NAME.__get__(type(value)))
    # Cut before escaping too: a huge name must not allocate a huge diagnostic.
    rendered = ascii(name[:_NAME_LIMIT])[1:-1]
    cut = len(name) > _NAME_LIMIT or len(rendered) > _NAME_LIMIT
    return rendered[:_NAME_LIMIT] + ("..." if cut else "")


def plain(value: object, name: str) -> str:
    """Return ``value`` as an exact ``str``; anything that is not a ``str`` is a ``TypeError``."""
    if not issubclass(type(value), str):
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
    raise OffsetError(f"unknown {name} (expected one of {expected})")
