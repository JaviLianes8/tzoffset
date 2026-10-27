# tzoffset 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to tzoffset. Nothing has been published on
PyPI under this name (`https://pypi.org/pypi/tzoffset/json` answered 404 on 2026-10-27), so
1.0.0 is the first release there and there is no installed base to upgrade; every change
against the `main` branch (0.2.0, af44df6) is still listed in the CHANGELOG.

Progress:
- [x] Branch `release/1.0.0` created from `main` (af44df6, 0.2.0)
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: RFCs and tz database fetched live, Java, PyPI package and stdlib oracles (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python on this PC (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [x] QA lenses round 1: 23 findings fixed (7989756, 5162d8a); see QA lenses
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)
- [x] PR #3 and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Scorecard (author)

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: 7 names; names, signatures, defaults and accepted values kept from 0.2.0 and pinned by `test_contract_api.py`; error type changes listed in CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS: `test_contract.py` checks `__all__` and `dir()`; README and GUIDE import only from `tzoffset` |
| 3 | Docstrings with runnable examples, doctests | PASS: 8 doctest items (module, 3 functions, `OffsetError`, 3 aliases); README (4 blocks) and GUIDE (3 blocks) run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed` shipped, `Literal` aliases, a consumer snippet type-checked in `test_typing.py`; no `Any` in the public API |
| 5 | Typed, documented, bounded errors | PASS: `OffsetError` (a `ValueError`), `TypeError` for wrong types; messages quote at most 40 characters; table in GUIDE |
| 6 | Contract tests of every public name | PASS: `test_contract.py`, `test_contract_api.py` (signatures, result types, error types, message bounds) |
| 7 | Real ground truth | PASS: see Ground truth |
| 8 | Real e2e from the wheel | PASS: wheel and sdist built, wheel installed in a throwaway venv, used from an empty folder, `tzoffset` and `python -m tzoffset` driven by subprocess; no PyPI release exists to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS: `test_fuzz.py`, `test_oracle.py` |
| 10 | Supported Pythons | PASS: 3.10 to 3.14 and both free-threaded builds; see Interpreters |
| 11 | README and `twine check` | PASS: `twine check --strict` on both files; absolute links checked by a test |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-26 |
| 13 | pyproject 1.0.0, Production/Stable | PASS: 1.0.0, `Development Status :: 5 - Production/Stable`, Python 3.10 to 3.14, MIT, Homepage, Source, Issues, Documentation, Changelog, no runtime dependencies |
| 14 | sdist and wheel contents | PASS: see Packaging |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending (orchestrator) |
| 17 | PR and trace guard | PR #3, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author round 28 of 28 killed |
| 19 | Five independent QA lenses | round 1 fixed (see QA lenses); re-verification by the lenses pending |

## API review (item 1)

The surface of 0.2.0 is kept: `parse_offset(text, *, grammar="lenient") -> timezone`,
`is_unknown_local_offset(text, *, grammar="lenient") -> bool`,
`format_offset(value, *, style="colon", zero="+") -> str`, `OffsetError(ValueError)` and
the `Grammar`, `Style` and `Zero` literal aliases. Options are keyword-only, so they can grow
without breaking calls. Fixed before freezing it:

- A non-`str` `grammar`, `style` or `zero` raised `OffsetError`; it is now always
  `TypeError`, matching the rule for `text`.
- A `tzinfo` whose `utcoffset(None)` returned a non-`timedelta` crashed with
  `AttributeError`; it is now `TypeError`.
- Messages quoted the whole input (a 1 MB argument gave a 1 MB message) and called the
  `repr` of the caller's object; they are now bounded and use only the characters.
- `OffsetError` showed and pickled as `tzoffset._errors.OffsetError`.
- The command line exited 0 when its reader closed early, read `--zone -foo` as an option,
  and printed a traceback for an `--at` beyond year 9999 in the zone.

## Ground truth (item 7)

Fetched sources, not committed, checked by size and SHA-256 against
`tests/vectors/sources/MANIFEST.txt` before every use (fetched 2026-10-18, fetched again on
2026-10-27 with identical hashes; tzdata 2026e still the latest release that day):

| Source | URL | Used for |
| --- | --- | --- |
| RFC 3339 | https://www.rfc-editor.org/rfc/rfc3339.txt | section 5.6 and Appendix A grammars (accepted sets compared exhaustively), 4.2 and 4.3 sentences, all six 5.8 examples, the Netherlands `+00:20` example |
| RFC 5322 | https://www.rfc-editor.org/rfc/rfc5322.txt | section 3.3 zone grammar, `+hhmm` arithmetic, `-0000` meaning |
| RFC 9557 | https://www.rfc-editor.org/rfc/rfc9557.txt | section 2: `Z` equals `-00:00`, no `-00:00` in ISO 8601; the Europe/Paris and New York examples through `zoneinfo` |
| tz database 2026e | https://data.iana.org/time-zones/releases/tzdata2026e.tar.gz | all 538 distinct standard offsets in the Zone lines round-trip in every style; extremes `-15:56:08` (Asia/Manila) and `15:13:42` (America/Metlakatla) |

Reference implementations run in this session:

- `java.time.ZoneOffset`, OpenJDK 21.0.8 (Temurin) on this PC, 2026-10-27:
  `scripts/oracle/ZoneOffsetOracle.java` through `scripts/java_oracle.py`, output recorded
  in `tests/vectors/java/zoneoffset.txt` (1,943 parse inputs, 3,475 offsets formatted).
  Parsing agrees except for four listed differences (one-digit hours, lower-case `z`,
  whitespace, magnitudes past 18 hours); the colon, compact, short and `Z` spellings agree
  on every offset.
- `rfc3339-validator` 0.1.4: the `rfc3339` grammar accepts exactly what it accepts on 6,814
  candidates, plus the lower-case `z` that RFC 3339 section 5.6 allows.
- `python-dateutil` 3.0.0 `isoparser().parse_tzstr`: every offset the `iso8601` grammar
  accepts reads to the same value; the only texts dateutil accepts beyond it are `-00`,
  `-0000` and `-00:00`, which RFC 9557 excludes from ISO 8601.
- Standard library: `strftime("%z")`, `isoformat()`, `strptime("%z")`, `fromisoformat`
  (60,000 seeded strings), `email.utils.parsedate_to_datetime` (`-0000` gives a naive
  datetime exactly when `is_unknown_local_offset` is true), `zoneinfo` over every zone from
  1800 to 2049.

Hand-written expectations (grammar tables in `test_grammar.py`, `test_parse.py`,
`test_format.py`) are labelled by being in those files; the expected sets in
`test_sources.py` are written from the RFC grammar lines that the same test finds in the
fetched text.

## Mutation round (item 18)

Each mutation applied alone to a fresh clone of 58a5244 and the whole suite run
(`pytest -x`, no wheel build); the first failing test is listed.

| # | Mutation | File | Result | First failing test |
| --- | --- | --- | --- | --- |
| 1 | hour limit off by one (23 to 24) | `_parse.py` | killed | `tests/test_contract_api.py::test_bad_values_raise_offset_error[<lambda>0]` |
| 2 | minute limit off by one (59 to 60) | `_parse.py` | killed | `tests/test_contract_api.py::test_bad_values_raise_offset_error[<lambda>2]` |
| 3 | second limit dropped | `_parse.py` | killed | `tests/test_grammar.py::test_every_grammar_rejects[+05:30:60-lenient]` |
| 4 | Unicode digits accepted (\d) | `_parse.py` | killed | `tests/test_fuzz.py::test_random_text_parses_or_raises_offset_error[lenient]` |
| 5 | lower-case z dropped | `_parse.py` | killed | `tests/test_cli_zone.py::test_at_reads_offsets_on_every_python[2026-03-08t07:00z-offset1]` |
| 6 | iso8601 negative zero allowed | `_parse.py` | killed | `tests/test_cli.py::test_grammar_option_is_applied` |
| 7 | negative zero not unknown | `_parse.py` | killed | `src/tzoffset/_parse.py::tzoffset._parse.is_unknown_local_offset` |
| 8 | sign ignored | `_parse.py` | killed | `src/tzoffset/__init__.py::tzoffset` |
| 9 | Unicode whitespace stripped | `_parse.py` | killed | `tests/test_fuzz.py::test_random_text_parses_or_raises_offset_error[lenient]` |
| 10 | strict grammar strips spaces | `_parse.py` | killed | `tests/test_docs.py::test_each_example_prints_what_its_comments_say[1]` |
| 11 | rfc3339 takes compact form | `_parse.py` | killed | `src/tzoffset/_parse.py::tzoffset._parse.parse_offset` |
| 12 | minutes and seconds swapped | `_format.py` | killed | `src/tzoffset/__init__.py::tzoffset` |
| 13 | day limit off by one (>= to >) | `_format.py` | killed | `tests/test_contract_api.py::test_bad_values_raise_offset_error[<lambda>3]` |
| 14 | fraction of a second accepted | `_format.py` | killed | `tests/test_contract_api.py::test_bad_values_raise_offset_error[<lambda>4]` |
| 15 | short style ignores seconds | `_format.py` | killed | `tests/test_format.py::test_format_short_with_seconds_keeps_every_field` |
| 16 | compact and colon separators swapped | `_format.py` | killed | `src/tzoffset/__init__.py::tzoffset` |
| 17 | zero minus spelling ignored | `_format.py` | killed | `tests/test_cli.py::test_zero_option[---00:00]` |
| 18 | seconds field always written | `_format.py` | killed | `src/tzoffset/__init__.py::tzoffset` |
| 19 | naive datetime gets wrong error type | `_format.py` | killed | `tests/test_contract_api.py::test_bad_values_raise_offset_error[<lambda>5]` |
| 20 | wrong value type gets OffsetError | `_format.py` | killed | `tests/test_contract_api.py::test_wrong_argument_types_raise_type_error[<lambda>6]` |
| 21 | non-str option gets OffsetError | `_checks.py` | killed | `tests/test_contract_api.py::test_wrong_argument_types_raise_type_error[<lambda>0]` |
| 22 | message quote limit removed | `_checks.py` | killed | `tests/test_cli_zone.py::test_huge_zone_and_at_values_are_cut_in_messages` |
| 23 | str subclass trusted | `_checks.py` | killed | `tests/test_contract_api.py::test_str_subclasses_are_read_by_their_characters` |
| 24 | CLI dash offsets not shielded | `_cli.py` | killed | `tests/test_cli.py::test_dash_led_offsets_are_shielded_from_argparse` |
| 25 | CLI closed pipe gives status 0 | `_cli.py` | killed | `tests/test_cli_output.py::test_a_reader_that_leaves_first_gets_status_one_and_no_noise[argv0]` |
| 26 | CLI pipe error while parsing gives status 0 | `_cli.py` | killed | `tests/test_cli_output.py::test_a_write_error_while_parsing_is_handled_like_one_while_printing` |
| 27 | CLI EINVAL not read as a closed pipe | `_cli.py` | killed | `tests/test_cli_output.py::test_a_reader_that_leaves_first_gets_status_one_and_no_noise[argv0]` |
| 28 | CLI naive --at read as local time | `_cli_zone.py` | killed | `tests/test_cli.py::test_zone_at_a_naive_moment_is_wall_time` |

28 of 28 killed, no survivor. Mutants 26 and 27 cover the closed-pipe handling added
in 58a5244 for Python 3.10.

## Interpreters (item 10)

Interpreters installed on this PC: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.13.11
free-threaded, 3.14.2 and 3.14.2 free-threaded (3.9 and below are outside
`requires-python`). This PC grants no heavy turn while it has under 10 GB of free memory,
so the matrix ran through `recurso.sh` on the PC of Elena with the same versions installed
by uv in a private folder: full suite, wheel e2e included (`TZOFFSET_E2E=1`), one
interpreter at a time, on a fresh clone of 58a5244 with the fetched sources copied in.

| Python | Result |
| --- | --- |
| 3.10.19 | 366 passed, 1 skipped (`fromisoformat` reads offsets only from 3.11) |
| 3.11.5 | 367 passed |
| 3.12.12 | 367 passed |
| 3.13.2 | 367 passed |
| 3.13.11 free-threaded | 357 passed, 2 skipped (`test_typing.py`: mypy has a dependency without a free-threaded 3.13 wheel) |
| 3.14.2 | 367 passed |
| 3.14.2 free-threaded | 367 passed |

The first run, at 05b9dd8, found a defect on 3.10 only: argparse there lets the write error
of `--help` or `--version` on a closed pipe escape as a `BrokenPipeError` traceback.
Fixed in 58a5244 (exit status 1, quiet) with a test that does not depend on the version.

## Packaging (item 14)

Built from a fresh clone of fc94c9d with `python -m build` (CPython 3.14, hatchling) and
checked with `twine check --strict`: both PASSED.

- Wheel `tzoffset-1.0.0-py3-none-any.whl`: the nine modules of `tzoffset/`, `py.typed`,
  `METADATA`, `WHEEL`, `entry_points.txt` (the `tzoffset` command), `licenses/LICENSE` and
  `RECORD`. No tests, data or scratch files.
- sdist `tzoffset-1.0.0.tar.gz`: `README.md`, `GUIDE.md`, `CHANGELOG.md`, `CONTRIBUTING.md`,
  `LICENSE`, `pyproject.toml`, `requirements-dev.txt`, `.gitignore`, `scripts/`, `src/` and
  `tests/`. Of `tests/vectors/` it holds only `sources/MANIFEST.txt` (URLs and hashes, no
  third-party text) and `java/zoneoffset.txt` (output of this project's own Java program);
  the fetched RFCs and the tz database tarball, `IMPROVEMENTS-round.md` and this report are
  left out, which `test_e2e_wheel.py` asserts.
- `METADATA`: version 1.0.0, `License-Expression: MIT`, `Requires-Python: >=3.10`, no
  `Requires-Dist` outside the `dev` extra, Production/Stable and Python 3.10 to 3.14
  classifiers, the README as the long description.

`test_e2e_wheel.py` builds both files again on every interpreter of the matrix at 58a5244
and asserts the same contents.

## Gates (item 15)

On 58a5244, ruff 0.17.3 and mypy 2.4.0 in a CPython 3.13.2 venv on this PC:
`ruff format --check .` exit 0 (35 files), `ruff check .` exit 0, `mypy --strict src` exit 0
(9 files), `mypy --strict src tests` exit 0 (27 files). `pytest` exit 0 on every interpreter
above; the configured `testpaths` include `src`, so the 8 doctest items run with it.

## PR

PR #3 (https://github.com/JaviLianes8/tzoffset/pull/3) from `release/1.0.0` to `main`;
the trace guard reports CLEAN on it. Merge and publish are left to the maintainer.

## QA lenses (item 19)

### Round 1

Five independent QA lenses reviewed 7dc5b6d: a (API and docs), b (correctness and
ground truth), c (adversarial), d (packaging and e2e), e (contract strength, own mutation
round). 23 findings, all fixed; none disputed. Each behaviour bug got a contract test first,
checked to fail on 7dc5b6d (on 3.10 and 3.11 for the version-bound ones) and to pass after
the fix.

| Lens | Id | Finding | Fix | Contract |
| --- | --- | --- | --- | --- |
| a | A-F1 | importing the package set `__doc__` on typing's shared `Literal` objects | aliases are no longer touched; their docs are `#:` comments, the `_types` docstring, a new GUIDE section and the `__test__` examples | `test_importing_leaves_the_shared_literal_objects_alone`, `test_every_alias_has_a_documented_example` |
| a, c | A-F2, C-F1 | an aware `datetime` whose `tzinfo` returns a day or more raised a plain `ValueError` | the offset is read from the stored `tzinfo` and range-checked by the library: `OffsetError` | `test_a_datetime_with_an_offset_of_a_day_or_more_is_an_offset_error` |
| a | A-F3 | "at most 40 characters" was promised for every argument, but a `timedelta` is shown whole | promise reworded in `OffsetError`, README and GUIDE: 40 characters of a text argument; an offset is shown as its exact `timedelta` | `test_offset_messages_show_the_exact_value` |
| a, b | A-F4, B-F1 | `--at` refused RFC 3339 fractions on 3.10 and called valid text "not ISO 8601" | seconds are respelled before `fromisoformat` (any fraction length, comma mark); GUIDE and `--help` state the forms and that the basic form needs 3.11; new message `cannot read --at as a date and time` | `test_cli_at.py`: RFC 3339 section 5.8 timestamps (also read from the fetched RFC), fractions, `_extended`, basic form per version |
| a | A-F5 | CONTRIBUTING said tests never touch time, disk or network | reworded to what the suite really reads, the one real-clock test and the e2e build | docs |
| a | A-F6 | CHANGELOG older entries not in Keep a Changelog form | 0.2.0 and 0.1.0 dated (2026-10-13, 2026-10-12, commit dates), `### Added` in 0.1.0, link references | docs |
| b | B-F2 | a leap second (second 60) was refused as "not ISO 8601" | second 60 is read as 59 of the same minute (documented in the GUIDE) | `test_rfc3339_examples_are_read_on_every_python`, `test_a_naive_leap_second_is_read_as_second_59` |
| c | C-F2 | a `datetime` subclass overriding `utcoffset` gave `AttributeError` | the stored `tzinfo` is read through the C-level field; the override is never called | `test_a_datetime_subclass_is_read_by_its_stored_tzinfo`, `test_a_datetime_subclass_cannot_swap_its_tzinfo` |
| c | C-F3 | `timedelta` subclasses were read through overridable fields | every offset is copied into an exact `timedelta` (`timedelta.__add__`) first | `test_a_timedelta_subclass_is_read_by_its_stored_value` |
| d | D1 | `tzoffset -- -05:30` refused on 3.10 and 3.11 | dash-led values after `--` are shielded too | `test_every_value_after_a_double_dash_is_an_offset`, updated `test_dash_led_offsets_are_shielded_from_argparse` and `test_double_dash_still_works` |
| d | D2 | sdist exclude list named `.gitignore`, which hatchling always ships | removed from the list with a comment; the e2e asserts every listed path is left out | `test_installed_wheel_end_to_end` |
| e | Z06 | `--zone` without `--at` not pinned to the zone | zones with a fixed offset for decades | `test_zone_without_at_is_the_offset_in_that_zone_now` |
| e | Z12 | the `fold=0` rule was unpinned | Europe/Madrid repeated and skipped 02:30 | `test_a_repeated_or_skipped_wall_time_takes_the_offset_before_the_change` |
| e | F25, F26 | `timedelta.__repr__(delta)` to `delta!r` survived | the subclass case is now pinned; after the C-F3 fix `delta` is always an exact `timedelta`, so this mutant is equivalent (the mutant that drops the exact copy is killed) | `test_offset_messages_show_the_exact_value`, `test_a_timedelta_subclass_is_read_by_its_stored_value` |
| e | F27 | `datetime.isoformat(value)` to `value.isoformat()` survived | pinned with a subclass whose `isoformat` is huge | `test_offset_messages_show_the_exact_value` |
| e | L10, L16, L17 | the 200-character cut of usage messages was unpinned | exact length, `...` ending and the 200/201 boundary | `test_a_long_usage_message_is_cut_to_two_hundred_characters`, `test_the_cut_starts_past_two_hundred_characters` |
| e | C02 | the 40-character quote boundary was unpinned | 40 and 41 characters | `test_a_text_of_forty_characters_is_quoted_whole` |
| e | P28 | the `TypeError` message was unpinned and named `offset` for the `text` parameter | it now says `text must be a str, not int`; every option message pinned | `test_type_errors_name_the_parameter` |

Lens c also noted (no finding) that exceptions raised by a caller's own `utcoffset`
propagate unchanged; that is kept. From the observations of lens a: `--help` now shows the
defaults of `--style` and `--grammar`; the README links to `blob/main` resolve only after
the merge, so they are to be checked then.

Mutation re-check of round 1, on 7989756, one mutant at a time, whole suite without the
wheel build (CPython 3.14.2 on the PC of Elena, `recurso.sh` turn):

| # | Mutation | Result |
| --- | --- | --- |
| 1 | Z06 zone without `--at` ignores the zone | killed: `test_cli_at.py::test_zone_without_at_is_the_offset_in_that_zone_now` |
| 2 | Z12 naive `--at` uses `fold=1` | killed: `test_cli_at.py::test_a_repeated_or_skipped_wall_time_takes_the_offset_before_the_change` |
| 3 | F25 range message uses `delta!r` | equivalent: `delta` is an exact `timedelta` |
| 4 | F26 fraction message uses `delta!r` | equivalent: as above |
| 5 | exact `timedelta` copy dropped | killed: `test_contract_values.py::test_a_timedelta_subclass_is_read_by_its_stored_value` |
| 6 | F27 naive message uses `value.isoformat()` | killed: `test_contract_values.py::test_offset_messages_show_the_exact_value` |
| 7 | L10 cut threshold 20,000 | killed: `test_cli_args.py::test_a_long_usage_message_is_cut_to_two_hundred_characters` |
| 8 | L16 message limit 600 | killed: same test |
| 9 | L17 cut without `...` | killed: same test |
| 10 | cut boundary `>` to `>=` | killed: `test_cli_args.py::test_the_cut_starts_past_two_hundred_characters` |
| 11 | C02 quote boundary `<=` to `<` | killed: `test_contract_values.py::test_a_text_of_forty_characters_is_quoted_whole` |
| 12 | P28 `TypeError` names `offset` | killed: `test_contract_values.py::test_type_errors_name_the_parameter` |
| 13 | A-F1 alias `__doc__` set again | killed: `test_contract_values.py::test_importing_leaves_the_shared_literal_objects_alone` |
| 14 | A-F2 datetime offset read by `value.utcoffset()` | killed: `test_contract_values.py::test_a_datetime_with_an_offset_of_a_day_or_more_is_an_offset_error` |
| 15 | C-F2 datetime `tzinfo` read by attribute | survived on 7989756; killed from 5162d8a by `test_contract_values.py::test_a_datetime_subclass_cannot_swap_its_tzinfo` |
| 16 | D1 values after `--` not shielded | killed: `test_cli.py::test_dash_led_offsets_are_shielded_from_argparse` |
| 17 | B-F2 leap second kept as 60 | killed: `test_cli_at.py::test_rfc3339_examples_are_read_on_every_python` |
| 18 | B-F1 fraction not padded | killed only on 3.10 on 7989756 (3.11 and later read any fraction); killed on every Python from 5162d8a by `test_cli_at.py::test_seconds_are_spelled_the_way_python_3_10_reads_them` |

Interpreter matrix on 7989756 (PC of Elena, `recurso.sh` turn, fresh clone with the fetched
sources, wheel e2e included): 3.10.19 419 passed and 1 skipped (`fromisoformat` reads
offsets only from 3.11); 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2 free-threaded 420
passed; 3.13.11 free-threaded 410 passed and 2 skipped (no mypy wheel).

Commits of the round: 7989756 (fixes, docs and contracts), 5162d8a (contracts for the two
re-check survivors), then this report.

### Disputed findings

None in round 1.
