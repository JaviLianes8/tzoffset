# tzoffset guide

The behaviour of every public name in detail. Each Python block below runs as a test: a
comment line after a `print` holds what it prints.

## Reading: `parse_offset` and its grammars

`parse_offset(text, *, grammar="lenient")` returns a `datetime.timezone` with a fixed
offset. A zero offset returns `datetime.timezone.utc` itself, so `is` comparisons work.
Rules shared by every grammar:

- `Z` or `z` means UTC. RFC 3339 section 5.6 allows the lower-case letter.
- The sign is an ASCII `+` or `-`. The minus sign U+2212 and the full-width plus are refused.
- Digits are ASCII `0` to `9`. Arabic-Indic, Devanagari and other Unicode digits are refused,
  although Python's `int()` and `strptime` accept them.
- Hours are two digits, `00` to `23`; minutes and seconds `00` to `59`. A one-digit hour
  (`+5`) and hour `24` are refused: Python cannot hold an offset of a day.

| grammar | accepts | rejects |
| --- | --- | --- |
| `"lenient"` (default) | `+hh`, `+hhmm`, `+hh:mm`, `+hhmmss`, `+hh:mm:ss`, ASCII whitespace around | `+hh:mmss`, `+hhmm:ss` |
| `"rfc3339"` | `+hh:mm` only (RFC 3339 section 5.6 `time-numoffset`) | everything else, whitespace included |
| `"iso8601"` | `+hh`, `+hhmm`, `+hh:mm` (RFC 3339 Appendix A) | seconds, whitespace, `-00`, `-0000`, `-00:00` |

The `iso8601` grammar refuses a negative zero because RFC 9557 section 2 notes that ISO
8601:2000 and later do not allow `-00:00`. Hour `24`, which Appendix A lists, is left out
for the same reason as everywhere: Python offsets stop short of a day.

```python
from tzoffset import OffsetError, parse_offset

print(parse_offset("+05:30:45").utcoffset(None))
# 5:30:45
print(parse_offset(" -0800\n").utcoffset(None))
# -1 day, 16:00:00
print(parse_offset("z") is parse_offset("-00:00"))
# True
for text, grammar in [("+05", "rfc3339"), ("-00:00", "iso8601"), ("+5", "lenient")]:
    try:
        parse_offset(text, grammar=grammar)
    except OffsetError as error:
        print(error)
# not a valid rfc3339 UTC offset: '+05'
# ISO 8601 does not allow a negative zero offset: '-00:00'
# not a valid lenient UTC offset: '+5'
```

## The unknown local offset: `is_unknown_local_offset`

RFC 3339 section 4.3 uses `-00:00` for "the time in UTC is known, the local offset is not",
and RFC 9557 section 2 gives `Z` the same meaning. `+00:00` keeps its old meaning: UTC is the
preferred reference point. RFC 5322 section 3.3 has the same pair for mail, `-0000` and
`+0000`. `parse_offset` returns `timezone.utc` for all of them because the instant is the
same; `is_unknown_local_offset(text, *, grammar="lenient")` tells them apart. It validates
the text first and raises the same errors as `parse_offset`.

```python
from tzoffset import is_unknown_local_offset

print([is_unknown_local_offset(text) for text in ["Z", "-00:00", "-0000", "-00"]])
# [True, True, True, True]
print([is_unknown_local_offset(text) for text in ["+00:00", "+0000", "-05:00"]])
# [False, False, False]
```

## Writing: `format_offset`

`format_offset(value, *, style="colon", zero="+")` takes:

- a `datetime.timedelta`;
- a `tzinfo` whose `utcoffset(None)` returns a fixed offset, such as `datetime.timezone`;
- an aware `datetime`: the offset in force at that moment, the way to format a
  `zoneinfo.ZoneInfo`, whose offset changes over time.

`style` is `"colon"` (`+05:30`), `"compact"` (`+0530`) or `"short"` (`+05` when minutes and
seconds are zero, otherwise the colon form). A seconds field is added only when the seconds
are not zero, in the style's own spelling: `+05:30:45`, `+053045`. `zero` writes a zero
offset as `+00:00` (`"+"`), `-00:00` (`"-"`) or `Z` (`"Z"`); other offsets ignore it.

```python
from datetime import timedelta

from tzoffset import format_offset

offset = timedelta(hours=-4, minutes=-56, seconds=-2)
print([format_offset(offset, style=style) for style in ["colon", "compact", "short"]])
# ['-04:56:02', '-045602', '-04:56:02']
print([format_offset(timedelta(0), style="compact", zero=zero) for zero in ["+", "-", "Z"]])
# ['+0000', '-0000', 'Z']
```

The colon style writes what `datetime.isoformat()` writes after the time, and the compact
style what `strftime("%z")` writes; the tests check both for every whole minute and for
offsets with seconds, and check all four spellings against `java.time.ZoneOffset`.

## Errors

| Call | Raises |
| --- | --- |
| text that is not an offset in the grammar, a field out of range | `OffsetError` |
| an unknown `grammar`, `style` or `zero` string | `OffsetError`, naming the accepted values |
| an offset of a day or more, or a fraction of a second | `OffsetError` |
| a naive `datetime`, or a `tzinfo` with no fixed offset (`utcoffset(None)` is `None`) | `OffsetError` |
| `text`, `grammar`, `style` or `zero` that is not a `str` | `TypeError` |
| a `value` that is not a `timedelta`, `tzinfo` or `datetime`; a `tzinfo` whose `utcoffset(None)` returns something else | `TypeError` |

`OffsetError` is a `ValueError`, so existing `except ValueError` handlers keep working. A
message quotes at most 40 characters of what was passed, followed by its length, so a huge
or hostile argument never becomes a huge message. A subclass of `str` is read by its
characters only: its own `strip`, `__eq__` or `__repr__` are never called.

## Command line

`tzoffset OFFSET...` rewrites each offset on its own line; `tzoffset --zone NAME [--at
MOMENT]` prints the offset of a tz database zone. Options may come before or after the
offsets, and an offset that starts with `-` is never read as an option.

| option | meaning |
| --- | --- |
| `-s`, `--style` | `colon` (default), `compact` or `short` |
| `-z`, `--zero` | `+` (default), `-` or `Z` |
| `-g`, `--grammar` | `lenient` (default), `rfc3339` or `iso8601`, for the OFFSET values |
| `--zone` | a tz database name such as `Europe/Madrid` |
| `--at` | an ISO 8601 moment for `--zone`, now when left out |

A naive `--at` is wall time in the zone; when the clock skips or repeats that wall time, the
offset in force before the change is used (`fold=0`). An `--at` with an offset is converted
to the zone first, and `Z` and compact offsets such as `+0900` work on every supported
Python. Exit status: 0 when everything was written, 1 when the reader closed the output
first (`tzoffset ... | head -1`), 2 for bad input or usage, with the reason on standard error.

## Limits

- Offsets of a day or more cannot be represented by Python and are refused both ways.
- `java.time.ZoneOffset` stops at plus or minus 18 hours; this library allows hours up to
  23, as the RFC 3339 grammar does.
- POSIX TZ strings (`EST5EDT,M3.2.0,M11.1.0`) and zone abbreviations (`EST`, `CEST`) are not
  offsets and are refused; `zoneinfo` handles named zones.
