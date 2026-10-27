# tzoffset

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Parse and format bare numeric UTC offsets (Z, +05:30, -0800) both ways.

## Install

```
pip install tzoffset
```

## Usage

`parse_offset` turns an offset string into a fixed-offset `datetime.timezone`;
`format_offset` writes one back in the style you choose.

```python
from datetime import timedelta

from tzoffset import format_offset, parse_offset

print(parse_offset("+05:30"))
# UTC+05:30
print(parse_offset("-0800").utcoffset(None))
# -1 day, 16:00:00
print(parse_offset("Z") == parse_offset("+00"))
# True
print(format_offset(parse_offset("+0930")))
# +09:30
print(format_offset(timedelta(hours=-8), style="compact"))
# -0800
print(format_offset(timedelta(hours=9), style="short"))
# +09
print(format_offset(timedelta(0), zero="Z"))
# Z
```

### Grammars

`parse_offset(text, grammar=...)` picks how strict the reading is. Digits are ASCII only,
hours go up to 23 and minutes and seconds up to 59 in every grammar. Anything else raises
`OffsetError`, a `ValueError`.

| grammar | accepts | rejects |
| --- | --- | --- |
| `"lenient"` (default) | `Z`, `z`, `+hh`, `+hhmm`, `+hh:mm`, `+hhmmss`, `+hh:mm:ss`, surrounding ASCII whitespace | mixed colon and compact forms |
| `"rfc3339"` | `Z`, `z`, `+hh:mm` (RFC 3339 section 5.6) | everything else, spaces included |
| `"iso8601"` | `Z`, `z`, `+hh`, `+hhmm`, `+hh:mm` (RFC 3339 Appendix A) | seconds, spaces, `-00`, `-0000`, `-00:00` |

```python
from tzoffset import OffsetError, parse_offset

print(parse_offset("+05:30:45").utcoffset(None))
# 5:30:45
for text in ["+0530", "+05:30:45", " +05:30"]:
    try:
        parse_offset(text, grammar="rfc3339")
    except OffsetError as error:
        print(error)
# not a valid rfc3339 UTC offset: '+0530'
# not a valid rfc3339 UTC offset: '+05:30:45'
# not a valid rfc3339 UTC offset: ' +05:30'
```

### Unknown local offset

RFC 3339 section 4.3, as updated by RFC 9557 section 2, gives `Z` and `-00:00` one meaning:
the UTC time is known and the local offset is not. `+00:00` instead says UTC is the
reference for the time; RFC 5322 gives mail the same pair, `-0000` and `+0000`. All of them
parse to UTC; `is_unknown_local_offset` keeps the difference, and `zero=` picks the
spelling when formatting.

```python
from datetime import datetime, timezone

from tzoffset import format_offset, is_unknown_local_offset

print(is_unknown_local_offset("-00:00"), is_unknown_local_offset("Z"))
# True True
print(is_unknown_local_offset("+00:00"))
# False
print(format_offset(timezone.utc, zero="-"))
# -00:00
print(format_offset(datetime(2026, 7, 1, 12, tzinfo=timezone.utc), zero="Z"))
# Z
```

### Zones

A `zoneinfo.ZoneInfo` has no single offset, so `format_offset` takes an aware `datetime`
and writes the offset in force at that moment. Offsets with seconds, such as the local mean
time the tz database keeps for years before standard time, are written with a seconds field
(`-04:56:02`); fractions of a second are refused. On Windows, `zoneinfo` needs the `tzdata`
package (`pip install tzdata`) to find any zone.

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from tzoffset import format_offset

print(format_offset(datetime(2026, 1, 15, tzinfo=ZoneInfo("Europe/Madrid"))))
# +01:00
print(format_offset(datetime(2026, 7, 15, tzinfo=ZoneInfo("Europe/Madrid"))))
# +02:00
print(format_offset(datetime(1800, 1, 1, tzinfo=ZoneInfo("America/New_York"))))
# -04:56:02
```

## Command line

```
$ tzoffset +0530 -08 Z
+05:30
-08:00
+00:00
$ tzoffset --style compact --zero Z +05:30 -00:00
+0530
Z
$ tzoffset --zone America/New_York --at 2026-03-08T12:00
-04:00
```

`--grammar` picks the input grammar, `--zone` with `--at` prints the offset of a tz
database zone at a moment (without `--at` it is now). `--at` takes RFC 3339 timestamps
such as `1985-04-12T23:20:50.52Z` on every supported Python; the GUIDE lists the other
forms. A naive `--at` is wall time in that zone; a wall time skipped or repeated by a clock change takes the offset in force before the
change (`fold=0`). Bad input exits with status 2, and a reader that closes the output
early (`| head`) gives status 1. Also available as `python -m tzoffset`.

## API

| Name | What it does |
| --- | --- |
| `parse_offset(text, *, grammar="lenient")` | A fixed-offset `datetime.timezone`; `timezone.utc` itself for a zero offset. |
| `is_unknown_local_offset(text, *, grammar="lenient")` | `True` for `Z` and a negative zero (`-00:00`, `-0000`, `-00`), after validating the text. |
| `format_offset(value, *, style="colon", zero="+")` | Text for a `timedelta`, a fixed-offset `tzinfo` or an aware `datetime`. |
| `Grammar`, `Style`, `Zero` | `Literal` aliases of the accepted `grammar`, `style` and `zero` values. |
| `OffsetError` | `ValueError` subclass for text that is not an offset and values out of range. Arguments of the wrong type raise `TypeError`. Messages quote at most 40 characters of a text argument. |

The [GUIDE](https://github.com/JaviLianes8/tzoffset/blob/main/GUIDE.md) has every rule in
detail, and the [CHANGELOG](https://github.com/JaviLianes8/tzoffset/blob/main/CHANGELOG.md)
what changed in each release.

## Why

Python can read and write an offset only as a side effect of something larger, and each
way has gaps (checked on CPython 3.10 to 3.14):

- `datetime.strptime(text, "%z")` returns a `datetime` of 1 January 1900 that carries the
  offset. It refuses `+05` and a lower-case `z`, and it accepts what protocols do not:
  Arabic-Indic digits (`+٠٥:30` reads as `+05:30`) and fractions of a second
  (`+05:30:45.5`). It reads `-00:00` as plain UTC, so the "local offset unknown" meaning of
  RFC 3339 is lost, and there is no strict mode.
- `datetime.fromisoformat` and `time.fromisoformat` need a date or a time in front of the
  offset and refuse a lower-case `z`, which RFC 3339 allows.
- `strftime("%z")` writes only `+0530`; `%:z` (`+05:30`) exists from Python 3.12. Neither
  writes `Z`, `-00:00` or the short `+05`, and `isoformat()` always writes `+00:00`.
- `python-dateutil` (3.0.0) has `isoparser().parse_tzstr`, which reads `++5` as `+05:00`
  and `+05:3` as `+05:03`, and has no seconds field.

`tzoffset` is small, typed and has no dependencies. It reads and writes the offset alone,
both ways, with a named grammar for RFC 3339 and for ISO 8601 and a lenient one for logs,
and it keeps `-00:00` apart from `+00:00`. It is tested against the texts of RFC 3339,
RFC 5322 and RFC 9557, the zone offsets of the tz database 2026e, `java.time.ZoneOffset`,
`rfc3339-validator`, `python-dateutil` and the standard library.

Not covered: POSIX TZ strings such as `EST5EDT,M3.2.0,M11.1.0` (rule sets with names and
an inverted sign; use `zoneinfo`), and offsets of a day or more, which Python cannot hold.

## Development

`python scripts/fetch_vectors.py` downloads the RFCs and the tz database release listed in
`tests/vectors/sources/MANIFEST.txt` and checks their SHA-256 (they are not part of the
repository; their tests skip without them). `python scripts/java_oracle.py` regenerates
the recorded `java.time.ZoneOffset` output with a JDK. `pip install -e .[dev]` installs the
tools and the reference parsers, `scripts/check.ps1` runs format, lint, types and tests,
and `TZOFFSET_E2E=1` also builds the wheel and tests the installed package and its command.

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/tzoffset/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
