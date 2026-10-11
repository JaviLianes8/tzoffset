# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release: `parse_offset`, `format_offset` and `OffsetError`.
- Parse `Z`, `+HH`, `+HHMM`, `+HH:MM` and their second-bearing forms into a `timezone`.
- Format a `timezone` or `timedelta` in `colon`, `compact` or `short` style.
