from __future__ import annotations

import importlib.resources
import pickle
import typing

import tzoffset

# The public API. Add every exported name here as the library grows; this list is the
# contract and the test below fails if the module and this list disagree.
PUBLIC_API: list[str] = [
    "Grammar",
    "OffsetError",
    "Style",
    "Zero",
    "format_offset",
    "is_unknown_local_offset",
    "parse_offset",
]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(tzoffset.__all__) == sorted(PUBLIC_API)


def test_nothing_else_is_public_at_the_package_top() -> None:
    public = [name for name in dir(tzoffset) if not name.startswith("_")]
    assert sorted(public) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in tzoffset.__all__:
        assert hasattr(tzoffset, name)


def test_version_is_a_three_part_string() -> None:
    parts = tzoffset.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("tzoffset").joinpath("py.typed").is_file()


def test_offset_error_is_a_value_error() -> None:
    assert issubclass(tzoffset.OffsetError, ValueError)


def test_offset_error_shows_and_pickles_under_the_package_name() -> None:
    assert tzoffset.OffsetError.__module__ == "tzoffset"
    assert b"tzoffset._errors" not in pickle.dumps(tzoffset.OffsetError("bad"))
    again = pickle.loads(pickle.dumps(tzoffset.OffsetError("bad")))
    assert (type(again), str(again)) == (tzoffset.OffsetError, "bad")


def test_the_literal_aliases_list_the_accepted_values() -> None:
    assert typing.get_args(tzoffset.Grammar) == ("lenient", "rfc3339", "iso8601")
    assert typing.get_args(tzoffset.Style) == ("colon", "compact", "short")
    assert typing.get_args(tzoffset.Zero) == ("+", "-", "Z")
