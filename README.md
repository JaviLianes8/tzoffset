# tzoffset

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
the UTC time is known and the local offset is not. `+00:00` instead says UTC is the reference
for the time. All three parse to UTC; `is_unknown_local_offset` keeps the difference, and `zero=` picks the spelling
when formatting.

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
database zone at a moment (without `--at` it is now). A naive `--at` is wall time in that
zone; a wall time skipped or repeated by a clock change takes the offset in force before the
change (`fold=0`). Bad input exits with status 2. Also available as `python -m tzoffset`.

## Why

The standard library parses a UTC offset only as part of a full timestamp:
`datetime.fromisoformat` needs a date, and `%z` works one direction and only on a
`datetime`. There is no stdlib call that turns a loose `"+05:30"` into a
`timezone`, nor a clean way to render one back in a chosen style. The usual
alternative, `dateutil`, is a large dependency, and its `tz.tzoffset` is a
`tzinfo` implementation, not a string codec. `tzoffset` is the small, typed,
zero-dependency piece that does just the offset string, both directions.

Not covered: POSIX TZ strings such as `EST5EDT,M3.2.0,M11.1.0` (rule sets with names and
an inverted sign; use `zoneinfo`), and offsets of a day or more, which Python cannot hold.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
