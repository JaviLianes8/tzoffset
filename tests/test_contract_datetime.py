"""Hand-written contracts for stored datetime fields and both sides of a repeated hour."""

from __future__ import annotations

from datetime import datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo

import pytest

from tzoffset import format_offset


class _Fields(datetime):
    def __getattribute__(self, name: str) -> object:
        if name in {"year", "month", "day", "hour", "minute", "second", "microsecond", "fold"}:
            return 9
        return super().__getattribute__(name)


def test_timezone_callbacks_receive_an_exact_datetime_with_stored_fields() -> None:
    seen: list[datetime] = []

    class Zone(tzinfo):
        def utcoffset(self, moment: datetime | None) -> timedelta:
            assert moment is not None
            seen.append(moment)
            return timedelta(hours=moment.hour)

        def dst(self, moment: datetime | None) -> None:
            return None

        def tzname(self, moment: datetime | None) -> None:
            return None

    zone = Zone()
    value = _Fields(2026, 2, 3, 1, 5, 6, 7, tzinfo=zone, fold=1)
    assert format_offset(value) == "+01:00"
    assert len(seen) == 1
    actual = seen[0]
    assert type(actual) is datetime
    assert (actual.year, actual.month, actual.day) == (2026, 2, 3)
    assert (actual.hour, actual.minute, actual.second, actual.microsecond) == (1, 5, 6, 7)
    assert actual.tzinfo is zone and actual.fold == 1


@pytest.mark.parametrize(("fold", "expected"), [(0, "+02:00"), (1, "+01:00")])
@pytest.mark.parametrize("cls", [datetime, _Fields])
def test_both_folds_of_an_ambiguous_aware_datetime_keep_their_offset(
    fold: int,
    expected: str,
    cls: type[datetime],
) -> None:
    zone = ZoneInfo("Europe/Madrid")
    ordinary = datetime(2026, 10, 25, 2, 30, tzinfo=zone, fold=fold)
    value = cls(2026, 10, 25, 2, 30, tzinfo=zone, fold=fold)
    assert ordinary.isoformat().endswith(expected)
    assert format_offset(value) == expected
