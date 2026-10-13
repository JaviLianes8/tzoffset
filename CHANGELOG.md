# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
