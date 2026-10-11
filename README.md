# tzoffset

Parse and format bare numeric UTC offsets (Z, +05:30, -0800) both ways.

## Install

```
pip install tzoffset
```

## Usage

```python
from datetime import timedelta, timezone

from tzoffset import format_offset, parse_offset

parse_offset("+05:30")        # timezone(timedelta(hours=5, minutes=30))
parse_offset("-0800")         # timezone(timedelta(hours=-8))
parse_offset("Z")             # timezone.utc
parse_offset("+09")           # timezone(timedelta(hours=9))
parse_offset("+05:30:45")     # offsets with seconds are accepted too

format_offset(timezone(timedelta(hours=9)))                   # "+09:00"
format_offset(timezone(timedelta(hours=9)), style="compact")  # "+0900"
format_offset(timezone(timedelta(hours=9)), style="short")    # "+09"
format_offset(timedelta(hours=-8))                            # "-08:00"
```

Accepted inputs: `Z`, `+HH`, `+HHMM`, `+HH:MM`, and the same with trailing
seconds (`+HHMMSS`, `+HH:MM:SS`). Colon and compact forms never mix. Fields and
the total magnitude are range checked, and anything invalid raises `OffsetError`
(a `ValueError`). Formatting takes a `timezone` or a `timedelta` and supports
three styles: `colon` (`+05:30`), `compact` (`+0530`) and `short` (`+09`, which
keeps the minutes when they are not zero).

## Why

The standard library parses a UTC offset only as part of a full timestamp:
`datetime.fromisoformat` needs a date, and `%z` works one direction and only on a
`datetime`. There is no stdlib call that turns a loose `"+05:30"` into a
`timezone`, nor a clean way to render one back in a chosen style. The usual
alternative, `dateutil`, is a large dependency, and its `tz.tzoffset` is a
`tzinfo` implementation, not a string codec. `tzoffset` is the small, typed,
zero-dependency piece that does just the offset string, both directions.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
