"""The --zone and --at side of the command line tool."""

from __future__ import annotations

import zoneinfo
from datetime import datetime, timedelta, timezone

import pytest

from tzoffset._cli import main
from tzoffset._cli_zone import moment


def _fails(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as stop:
        main(list(argv))
    assert stop.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    return captured.err


def _need_zones() -> None:
    try:
        zoneinfo.ZoneInfo("America/New_York")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no time zone database")


@pytest.mark.parametrize(
    ("text", "offset"),
    [
        ("2026-03-08T07:00Z", timedelta(0)),
        ("2026-03-08t07:00z", timedelta(0)),
        ("2026-03-08T07:00+0900", timedelta(hours=9)),
        ("2026-03-08T07:00+09", timedelta(hours=9)),
        ("2026-03-08T07:00:00-05:30", timedelta(hours=-5, minutes=-30)),
        ("2026-03-08 07:00:00.500+01:00", timedelta(hours=1)),
        ("2026-03-08T07:00-00:00", timedelta(0)),
    ],
)
def test_at_reads_offsets_on_every_python(text: str, offset: timedelta) -> None:
    when = moment(text)
    assert when.utcoffset() == offset
    assert when.replace(tzinfo=None, microsecond=0) == datetime(2026, 3, 8, 7)


@pytest.mark.parametrize("text", ["2026-03-08T07:00", "2026-03-08", "2026-03-08T07"])
def test_at_without_offset_is_naive(text: str) -> None:
    assert moment(text).tzinfo is None
    assert moment(text).date() == datetime(2026, 3, 8).date()


@pytest.mark.parametrize("text", ["2026-03-08T07:00+25:00", "2026-03-08T07:00+09:0", "noon"])
def test_at_rejects_bad_text(text: str) -> None:
    with pytest.raises(ValueError):
        moment(text)


def test_missing_database_is_named(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing(name: str) -> zoneinfo.ZoneInfo:
        raise zoneinfo.ZoneInfoNotFoundError(name)

    monkeypatch.setattr(zoneinfo, "ZoneInfo", missing)
    monkeypatch.setattr(zoneinfo, "available_timezones", set)
    assert "install the tzdata package" in _fails(capsys, "--zone", "Europe/Madrid")


def test_unknown_name_with_a_database_is_blamed_on_the_name(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing(name: str) -> zoneinfo.ZoneInfo:
        raise zoneinfo.ZoneInfoNotFoundError(name)

    monkeypatch.setattr(zoneinfo, "ZoneInfo", missing)
    monkeypatch.setattr(zoneinfo, "available_timezones", lambda: {"UTC"})
    assert "unknown time zone: 'Mars/Olympus'" in _fails(capsys, "--zone", "Mars/Olympus")


def test_a_folder_of_the_database_is_not_a_zone(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def folder(name: str) -> zoneinfo.ZoneInfo:
        raise IsADirectoryError(name)

    monkeypatch.setattr(zoneinfo, "ZoneInfo", folder)
    monkeypatch.setattr(zoneinfo, "available_timezones", lambda: {"America/New_York"})
    assert "unknown time zone: 'America'" in _fails(capsys, "--zone", "America")


def test_a_real_folder_name_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    for name in ("America", "Etc"):
        assert "unknown time zone" in _fails(capsys, "--zone", name)


def test_at_with_z_converts_on_every_python(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    for at, expected in [("2026-03-08T07:00z", "-04:00"), ("2026-03-08T15:59+0900", "-05:00")]:
        assert main(["--zone", "America/New_York", "--at", at]) == 0
        assert capsys.readouterr().out.split() == [expected]


def test_moment_keeps_the_utc_singleton() -> None:
    assert moment("2026-03-08T07:00Z").tzinfo is timezone.utc


@pytest.mark.parametrize(
    ("zone", "at"),
    [
        ("America/New_York", "0001-01-01T00:00+05:00"),
        ("Asia/Tokyo", "9999-12-31T23:59-05:00"),
        ("Etc/GMT-14", "9999-12-31T23:59Z"),
    ],
)
def test_an_instant_past_the_calendar_in_the_zone_exits_two(
    capsys: pytest.CaptureFixture[str], zone: str, at: str
) -> None:
    _need_zones()
    assert "--at is out of range in" in _fails(capsys, "--zone", zone, "--at", at)


def test_the_ends_of_the_calendar_still_work_as_wall_time(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _need_zones()
    assert main(["--zone", "America/New_York", "--at", "0001-01-01T00:00"]) == 0
    assert main(["--zone", "Asia/Tokyo", "--at", "9999-12-31T23:59"]) == 0
    assert capsys.readouterr().out.split() == ["-04:56:02", "+09:00"]


def test_dash_led_zone_and_at_values_arrive_intact(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    assert "unknown time zone: '-05'" in _fails(capsys, "--zone", "-05")
    assert "'-2026-01-01'" in _fails(capsys, "--zone", "UTC", "--at", "-2026-01-01")


def test_huge_zone_and_at_values_are_cut_in_messages(capsys: pytest.CaptureFixture[str]) -> None:
    _need_zones()
    for argv in (["--zone", "Z" * 100_000], ["--zone", "UTC", "--at", "2" * 100_000]):
        err = _fails(capsys, *argv)
        assert "(100000 characters)" in err
        assert len(err) < 1000
