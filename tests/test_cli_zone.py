"""The --zone and --at side of the command line tool."""

from __future__ import annotations

import zoneinfo
from datetime import datetime, timedelta, timezone

import pytest

from tzoffset._cli import _moment, main


def _fails(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as stop:
        main(list(argv))
    assert stop.value.code == 2
    return capsys.readouterr().err


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
    moment = _moment(text)
    assert moment.utcoffset() == offset
    assert moment.replace(tzinfo=None, microsecond=0) == datetime(2026, 3, 8, 7)


@pytest.mark.parametrize("text", ["2026-03-08T07:00", "2026-03-08", "2026-03-08T07"])
def test_at_without_offset_is_naive(text: str) -> None:
    assert _moment(text).tzinfo is None
    assert _moment(text).date() == datetime(2026, 3, 8).date()


@pytest.mark.parametrize("text", ["2026-03-08T07:00+25:00", "2026-03-08T07:00+09:0", "noon"])
def test_at_rejects_bad_text(text: str) -> None:
    with pytest.raises(ValueError):
        _moment(text)


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
    try:
        zoneinfo.ZoneInfo("America/New_York")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no time zone database")
    for name in ("America", "Etc"):
        assert "unknown time zone" in _fails(capsys, "--zone", name)


def test_at_with_z_converts_on_every_python(capsys: pytest.CaptureFixture[str]) -> None:
    try:
        zoneinfo.ZoneInfo("America/New_York")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no time zone database")
    for at, expected in [("2026-03-08T07:00z", "-04:00"), ("2026-03-08T15:59+0900", "-05:00")]:
        assert main(["--zone", "America/New_York", "--at", at]) == 0
        assert capsys.readouterr().out.split() == [expected]


def test_moment_keeps_the_utc_singleton() -> None:
    assert _moment("2026-03-08T07:00Z").tzinfo is timezone.utc
