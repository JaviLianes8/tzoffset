# tzoffset improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] ASCII-only digits and type checks on input
- [x] Named grammars: `lenient`, `rfc3339`, `iso8601`
- [x] Unknown local offset (`Z`, `-00:00`) and the `zero` choice when formatting
- [x] Format from an aware `datetime` or any fixed `tzinfo` (zoneinfo interplay)
- [x] Typed API: `Grammar`, `Style`, `Zero` aliases
- [x] Command line tool (`tzoffset`, `python -m tzoffset`)
- [x] Contracts: RFC citations, tz database offsets, stdlib oracles, typing, README, wheel e2e
- [ ] Mutation run (guards changed one at a time, each must fail the suite)
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` (not on PyPI) ships `parse_offset`, `format_offset` and `OffsetError`. It reads `Z`,
`+hh`, `+hhmm`, `+hh:mm` and the same with seconds, and writes colon, compact and short
styles. Read as a user who parses timestamps from logs, APIs and mail headers:

- `\d` in the pattern matches any Unicode digit, so `+05:30` written with Arabic-Indic
  digits parses. Offsets in protocols are ASCII.
- One grammar only. There is no way to ask for exactly what RFC 3339 allows (`Z` or `+hh:mm`)
  or exactly what ISO 8601 allows (no seconds, no `-00:00`).
- `-00:00` is read as UTC with no way to tell it apart from `+00:00`, although RFC 3339 gives it
  its own meaning; `Z` cannot be produced when formatting.
- A non-string to `parse_offset` or a non-offset to `format_offset` fails with an
  `AttributeError` from deep inside.
- `format_offset` takes a `timezone` or `timedelta` but not an aware `datetime`, which is the
  only way to get the offset of a `zoneinfo.ZoneInfo` at a given moment.
- `style` is a plain `str`, so mypy cannot catch `style="iso"`.
- No command line tool, README examples not executed, no wheel test, no ground truth in the tests.

## Sources (fetched 2026-10-13)

- RFC 3339, https://www.rfc-editor.org/rfc/rfc3339.txt (sha256 9ab2b886...):
  - 5.6: `time-numoffset = ("+" / "-") time-hour ":" time-minute`, `time-offset = "Z" /
    time-numoffset`, hours 00-23, minutes 00-59; a lower-case `z` is allowed, upper case
    should be generated.
  - 4.3: `-00:00` says the UTC time is known but the local offset is not.
  - Appendix A (the ISO 8601 grammar as collected there): `time-numoffset = ("+" / "-")
    time-hour [[":"] time-minute]`, so `+hh`, `+hhmm` and `+hh:mm`, no seconds.
- RFC 9557, https://www.rfc-editor.org/rfc/rfc9557.txt (sha256 87fa632c...), section 2: updates
  RFC 3339 4.3 so that `Z` carries the "local offset unknown" meaning, the same as `-00:00`;
  `+00:00` keeps meaning UTC is the preferred reference; ISO 8601:2000 and later do not allow
  `-00:00`.
- tz database 2026e, https://data.iana.org/time-zones/releases/tzdata2026e.tar.gz (sha256
  b2688280...): 538 distinct standard offsets in the Zone lines, 446 of them with seconds (local
  mean time), from `-15:56:08` (Asia/Manila) to `+15:13:42` (America/Metlakatla); no fractional
  seconds in the data; Etc/GMT-14 is `+14` and Etc/GMT+12 is `-12`.
- Python `datetime` docs, https://docs.python.org/3/library/datetime.html: a `utcoffset()` must
  be strictly between minus and plus 24 hours; since 3.7 it need not be a whole number of
  minutes; `%z` writes `+HHMM[SS[.ffffff]]` and `%:z` (3.12) the same with colons.
- The RFC texts and the tz tarball are third-party and not committed:
  `scripts/fetch_vectors.py` fetches them into a gitignored folder checked against a tracked
  MANIFEST; the tests that read them skip when the folder is absent.

## Ranked improvements

1. **ASCII digits only.** The pattern takes `[0-9]`; any other digit is rejected.
2. **Named grammars.** `parse_offset(text, grammar="lenient")` keeps the 0.1 behaviour;
   `"rfc3339"` takes exactly `Z`, `z` and `+hh:mm`; `"iso8601"` takes `Z`, `z`, `+hh`, `+hhmm`
   and `+hh:mm` and rejects `-00`, `-0000`, `-00:00`. Strict grammars do not strip spaces. An
   `+24:00` (allowed by the Appendix A hour range) cannot be a Python offset and is rejected.
3. **Unknown local offset.** `is_unknown_local_offset(text)` tells `Z` and `-00:00` (all
   spellings) from `+00:00`, as RFC 9557 reads them, after validating the text.
   `format_offset(..., zero="Z")` writes `Z` for a zero offset and `zero="-"` writes `-00:00`.
4. **Formatting from what users hold.** `format_offset` accepts an aware `datetime` (its
   `utcoffset()`, the way to format a `ZoneInfo` at a moment) and any `tzinfo` with a fixed
   offset; a zone without one gets a clear error pointing at the datetime form.
5. **Clean failures.** `TypeError` for wrong argument types, `OffsetError` (a `ValueError`)
   for bad text, out of range values, sub-second offsets and unknown options.
6. **Typed API.** `Grammar`, `Style` and `Zero` literal aliases exported; a mypy snippet test
   proves bad calls are rejected.
7. **Command line tool.** `tzoffset OFFSET... [--style] [--zero] [--grammar]` normalises
   offsets one per line; `tzoffset --zone NAME --at DATETIME` prints the offset of a tz
   database zone at that moment. Exit 2 on bad input, quiet on a closed pipe.
8. **Contracts that bite.** Grammar lines checked against the fetched RFC texts, every tz
   database offset round trips, `strptime("%z")` and `fromisoformat` as stdlib oracles,
   zoneinfo offsets across all zones, exhaustive round trip over whole minutes, executed README
   examples, an installed-wheel e2e and a mutation run.
9. **Docs and packaging.** README with the grammar table, CHANGELOG 0.2.0, classifiers and
   keywords, console script.

Left out on purpose: POSIX TZ strings (`EST5EDT,M3.2.0,M11.1.0` are rule sets with names and
inverted signs, not offsets; `zoneinfo` and the tz database cover them), fractional-second
offsets (no protocol grammar has them and the tz data no longer holds any), and offsets of a
day or more (Python cannot represent them).
