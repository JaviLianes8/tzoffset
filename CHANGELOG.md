# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-26

The first release on PyPI (0.1.0 and 0.2.0 were never uploaded). The public API is stable
from here on and follows Semantic Versioning: `parse_offset`, `is_unknown_local_offset`,
`format_offset`, `OffsetError`, `Grammar`, `Style` and `Zero`, with the names, signatures,
defaults and accepted values of 0.2.0.

### Added

- `GUIDE.md` with every rule in detail; every public name has a docstring with a runnable
  example, and the README and GUIDE examples run as tests.
- Tests against independent references: the texts of RFC 3339, RFC 5322 and RFC 9557, the
  zone offsets of the tz database 2026e, recorded `java.time.ZoneOffset` output,
  `rfc3339-validator`, `python-dateutil` and the standard library (`strptime`, `strftime`,
  `isoformat`, `fromisoformat`, `email.utils`, `zoneinfo`), plus seeded fuzz tests.

### Changed

- A `grammar`, `style` or `zero` that is not a `str` raises `TypeError` instead of
  `OffsetError`; an unknown string still raises `OffsetError`, which now names the accepted
  values.
- A `tzinfo` whose `utcoffset(None)` returns something other than a `timedelta` or `None`
  raises `TypeError` from `format_offset`.
- Error messages quote at most 40 characters of the input, followed by its length, and
  never call the `repr` of the caller's object; a field out of range names the allowed
  ranges.
- A subclass of `str` is read by its characters only; its own methods are not called.
- `OffsetError` shows and pickles as `tzoffset.OffsetError`.
- Command line: a reader that closes the output early (`| head`) gives exit status 1
  instead of 0, also for `--help` and `--version`; `--zone` and `--at` values that start
  with `-` are read as values; an `--at` that falls outside years 1 to 9999 in the zone
  exits with status 2 and a message instead of a traceback; usage messages are cut to
  200 characters.

## [0.2.0]

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

## [0.1.0]

- First release: `parse_offset`, `format_offset` and `OffsetError`.
- Parse `Z`, `+HH`, `+HHMM`, `+HH:MM` and their second-bearing forms into a `timezone`.
- Format a `timezone` or `timedelta` in `colon`, `compact` or `short` style.
