# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-01

The public API is stable from here on and follows Semantic Versioning:
`parse_offset`, `is_unknown_local_offset`,
`format_offset`, `OffsetError`, `Grammar`, `Style` and `Zero`, with the names, signatures,
defaults and accepted values of 0.2.0.

### Added

- `GUIDE.md` with every rule in detail; public functions and `OffsetError` have runnable
  docstrings. The shared `Literal` aliases `Grammar`, `Style` and `Zero` have runnable
  examples in the GUIDE and named alias doctests, without assigning their `__doc__`.
  The README and GUIDE examples run as tests.
- Tests against independent references: the texts of RFC 3339, RFC 5322 and RFC 9557, the
  zone offsets of the tz database 2026e, recorded `java.time.ZoneOffset` output,
  `rfc3339-validator`, `python-dateutil` and the standard library (`strptime`, `strftime`,
  `isoformat`, `fromisoformat`, `email.utils`, `zoneinfo`), plus seeded fuzz tests.
- An installed-wheel upgrade test from PyPI 0.2.0, comparing the stable API and command
  line before and after the upgrade in the same environment.
- Contracts for both folds of an ambiguous aware datetime, whitespace-padded options,
  and string subclasses overriding `__str__`.

### Changed

- A `grammar`, `style` or `zero` that is not a `str` raises `TypeError` instead of
  `OffsetError`; an unknown string still raises `OffsetError`, which now names the accepted
  values.
- A `tzinfo` whose `utcoffset` returns something other than a `timedelta` or `None`
  raises `TypeError` from `format_offset`, also when it is the `tzinfo` of an aware
  `datetime`.
- `format_offset` of an aware `datetime` whose `tzinfo` returns an offset of a day or more
  raises `OffsetError`, as the `tzinfo` itself does, instead of the plain `ValueError` of
  the standard library.
- Error messages omit supplied text arguments, including CLI values and unknown option
  names, to avoid echoing credentials. CLI syntax errors say `invalid command line
  arguments; see --help`. An offset is shown as its exact `timedelta`; a field out of
  range names the allowed ranges. The `TypeError` for a `text` that is not a `str` names
  the parameter: `text must be a str, not int` (it said `offset`). Stored type names bypass
  metaclass hooks and are escaped before being cut to 40 rendered characters plus `...`.
- A subclass of `str` is read by its characters only; its own methods are not called. A
  subclass of `timedelta` or `datetime` is read by its stored value: an overridden `days`,
  `seconds`, `utcoffset`, `__add__`, `__radd__` or `__repr__` no longer changes the result
  or the message. An object that only claims to be a `str`, `timedelta`, `tzinfo` or
  `datetime` through its `__class__`, such as `unittest.mock.Mock(spec=timedelta)`, raises
  `TypeError` (also when a `tzinfo` returns it). The `tzinfo` of a `datetime` is asked
  for its offset once: the message for a naive `datetime` is built from its stored fields.
  All argument checks
  use real types without evaluating an argument's `__class__` property. The timezone
  callback receives an exact `datetime` with the stored fields, timezone and `fold`,
  preventing subclass properties from changing the offset. The original object's
  identity and subclass-specific attributes are not passed to the callback.
- `OffsetError` shows and pickles as `tzoffset.OffsetError`.
- Command line: a reader that closes the output early (`| head`) gives exit status 1
  instead of 0, also for `--help` and `--version`; `--zone` and `--at` values that start
  with a dash followed by an ASCII digit are read as values; other dash-prefixed option
  values require the equals form (`--zone=-bad`, `--at=-bad`). An `--at` that falls outside
  years 1 to 9999 in the zone exits with status 2 and a message instead of a traceback;
  usage messages are cut to 200 characters. Values after `--` are offsets on every Python
  (3.10 and 3.11 refused
  `tzoffset -- -05:30`). Rejected option values are omitted from diagnostics.
- Command line `--at`: a fraction of a second of any length, a comma as the decimal mark
  and a leap second (second 60, read as 59) are read on every Python, so every RFC 3339
  timestamp works on 3.10 too; text it cannot read gives `cannot read --at as a date and
  time` instead of calling it not ISO 8601. `--help` shows the default style and grammar.
- The release script checks whether version 1.0.0 exists on PyPI, allowing an upgrade
  from an earlier release under the same package name.

## [0.2.0] - 2026-10-13

### Added

- `grammar=` on `parse_offset`: `"lenient"` (the default, unchanged), `"rfc3339"` (`Z` and
  `+hh:mm` only, RFC 3339 section 5.6) and `"iso8601"` (`Z`, `+hh`, `+hhmm`, `+hh:mm`, no
  negative zero, RFC 3339 Appendix A).
- `is_unknown_local_offset` tells `Z` and `-00:00` from `+00:00` (RFC 3339 section 4.3 as
  updated by RFC 9557 section 2).
- `zero=` on `format_offset` writes a zero offset as `+00:00`, `-00:00` or `Z`.
- `format_offset` takes an aware `datetime` (the way to format a `zoneinfo.ZoneInfo` at a
  moment) and any `tzinfo` with a fixed offset.
- `Grammar`, `Style` and `Zero` literal aliases for type checkers.
- Command line tool `tzoffset` (also `python -m tzoffset`): rewrite offsets in one style, or
  print the offset of a tz database zone at a moment.

### Changed

- Only ASCII digits are accepted; other Unicode digits used to parse.
- The lenient grammar strips only ASCII whitespace around the offset, not other Unicode spaces.
- A non-string to `parse_offset`, or a value that is not a `timedelta`, `tzinfo` or
  `datetime` to `format_offset`, raises `TypeError` instead of an `AttributeError`.

## [0.1.0] - 2026-10-12

### Added

- First version: `parse_offset`, `format_offset` and `OffsetError`.
- Parse `Z`, `+HH`, `+HHMM`, `+HH:MM` and their second-bearing forms into a `timezone`.
- Format a `timezone` or `timedelta` in `colon`, `compact` or `short` style.

[Unreleased]: https://github.com/JaviLianes8/tzoffset/commits/main
[1.0.0]: https://github.com/JaviLianes8/tzoffset/compare/af44df6...main
[0.2.0]: https://github.com/JaviLianes8/tzoffset/compare/6651c8a...af44df6
[0.1.0]: https://github.com/JaviLianes8/tzoffset/commit/6651c8a
