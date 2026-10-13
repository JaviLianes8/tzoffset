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
- [x] Mutation run (guards changed one at a time, each must fail the suite)
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [x] Independent review findings fixed with regression tests
- [x] Pull request opened, guard clean

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

## Verification

- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` (also `src tests`) and
  `pytest` exit 0 on a second machine with Python 3.14, a fresh clone, `tzdata` installed, the
  sources fetched by the script and `TZOFFSET_E2E=1`: 263 passed, nothing skipped. The wheel
  test builds the wheel and the sdist, checks that no fetched source or test ships in them,
  installs the wheel in a fresh venv, drives the API from an empty folder, and runs the
  installed `tzoffset` script and `python -m tzoffset`. Locally (Python 3.13, no `tzdata`) the
  zone tests skip cleanly.
- Ground truth: the grammar lines of RFC 3339 (5.6, 4.3, Appendix A) and RFC 9557 section 2
  are read from the fetched texts, and both strict grammars are compared exhaustively with the
  sets those rules give (every sign, hour 00-25 and minute 00-61, with and without a colon).
  All 538 standard offsets of the tz database 2026e Zone lines round trip in every style.
- Oracles: `strftime("%z")`, `isoformat`, `strptime("%z")` and `fromisoformat` (60000 fuzzed
  strings) agree with the library; every zone in `zoneinfo` from 1800 to 2050 formats and
  parses back to its own `utcoffset()`.
- Mutations: 61 mutants (each pattern of the three grammars, ASCII digits and whitespace, the
  field ranges, the negative zero and unknown offset rules, every type and option check, the
  zero spellings, styles, seconds field and day limit when formatting, and every command line
  rule: the argparse shield, intermixed options, `--zone`/`--at` checks, zone errors, the
  pre-3.11 offset reading of `--at`, exit codes and the closed pipe), applied one at a time
  with the bytecode cache disabled and purged before each run, baseline green before and
  after. The first run left two alive: Unicode digits in the minute field (no test had them
  there) and the argparse shield (Python 3.13 and later read `-08:00` as a negative number by
  themselves, so only a direct test catches it on new versions). Both got tests; the final run
  killed all 61.
- Independent review: 9 findings, all fixed with regression tests: the README zone example
  depended on the platform tz data (now America/New_York in 1800, `-04:56:02`); `--zone` with
  a folder such as `America` crashed (now exit 2); `--at` with `Z` or `+0900` failed before
  Python 3.11 (the offset is now read by this library); a missing tz database was reported as
  an unknown zone (now named, with the fix); the test parser of the tz data skipped one zone
  block after a blank line (now 538 offsets, `0:29:46` included); the RFC line checks now also
  drive the parser; README paraphrases no longer sit in quotation marks and the cited test
  phrases carry their URLs; the lenient grammar strips ASCII whitespace only; the checklist
  above is kept current. The `fold=0` reading of a naive `--at` in a gap or overlap is now
  documented.
