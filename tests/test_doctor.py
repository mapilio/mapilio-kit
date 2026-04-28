"""Unit tests for ``mapilio_kit.components.utilities.doctor``.

These tests exercise the individual checks with mocks so they don't depend
on whether ffmpeg / exiftool / a Mapilio account exist on the host.
"""

from __future__ import annotations

import json
from collections import namedtuple

import pytest

from mapilio_kit.components.utilities.doctor import (
    FAIL,
    OK,
    WARN,
    CheckResult,
    DoctorReport,
    check_credentials,
    check_disk_space,
    check_exiftool,
    check_ffmpeg,
    check_kit_version,
    check_python_version,
    check_telemetry,
    render_text,
    run_all_checks,
)

# ----------------------------- python check ----------------------------- #


def test_python_check_ok_for_supported_version() -> None:
    result = check_python_version(version_info=(3, 11, 1), minimum=(3, 8))
    assert result.status == OK
    assert "3.11.1" in result.message


def test_python_check_fails_for_too_old() -> None:
    result = check_python_version(version_info=(3, 6, 9), minimum=(3, 8))
    assert result.status == FAIL


# ---------------------------- kit version ------------------------------- #


def test_kit_version_check_always_ok() -> None:
    result = check_kit_version("9.9.9")
    assert result.status == OK
    assert result.details["version"] == "9.9.9"


# ----------------------- external binaries (mocked) --------------------- #


def _make_runner(rc: int, stdout: str = "", stderr: str = ""):
    def _runner(_cmd):
        return rc, stdout, stderr
    return _runner


def test_ffmpeg_missing_is_fail() -> None:
    result = check_ffmpeg(runner=_make_runner(0), which=lambda _: None)
    assert result.status == FAIL
    assert "not found" in result.message


def test_ffmpeg_present_and_modern_is_ok() -> None:
    result = check_ffmpeg(
        runner=_make_runner(0, "ffmpeg version 6.1.1 Copyright ..."),
        which=lambda _: "/usr/bin/ffmpeg",
    )
    assert result.status == OK
    assert "6.1" in result.message


def test_ffmpeg_too_old_is_warn() -> None:
    result = check_ffmpeg(
        runner=_make_runner(0, "ffmpeg version 2.8.5"),
        which=lambda _: "/usr/bin/ffmpeg",
    )
    assert result.status == WARN


def test_ffmpeg_unparseable_version_is_warn() -> None:
    result = check_ffmpeg(
        runner=_make_runner(0, "ffmpeg version <unknown> built ..."),
        which=lambda _: "/usr/bin/ffmpeg",
    )
    assert result.status == WARN


def test_exiftool_modern_version_is_ok() -> None:
    result = check_exiftool(
        runner=_make_runner(0, "12.78\n"),
        which=lambda _: "/usr/bin/exiftool",
    )
    assert result.status == OK


# ------------------------------ disk ------------------------------------ #


_Usage = namedtuple("Usage", "total used free")


def test_disk_space_ok_when_above_threshold() -> None:
    result = check_disk_space(
        path=".",
        minimum_bytes=100,
        disk_usage=lambda _: _Usage(1000, 500, 500),
    )
    assert result.status == OK


def test_disk_space_warn_when_below_threshold() -> None:
    result = check_disk_space(
        path=".",
        minimum_bytes=10_000_000_000,
        disk_usage=lambda _: _Usage(1000, 500, 500),
    )
    assert result.status == WARN


def test_disk_space_warn_on_oserror() -> None:
    def _raises(_path):
        raise OSError("nope")

    result = check_disk_space(path="/nonexistent", disk_usage=_raises)
    assert result.status == WARN
    assert "nope" in result.message


# ----------------------------- credentials ------------------------------ #


def test_credentials_ok_with_users() -> None:
    result = check_credentials(user_loader=lambda: [
        {"SettingsEmail": "alice@example.com", "SettingsUsername": "alice"},
    ])
    assert result.status == OK
    assert "alice@example.com" in result.message


def test_credentials_warn_when_no_valid_user() -> None:
    result = check_credentials(user_loader=lambda: [
        {"SettingsUsername": "alice"},  # missing SettingsEmail
    ])
    assert result.status == WARN
    assert result.details["user_count"] == 0


def test_credentials_warn_on_loader_failure() -> None:
    def _raises():
        raise RuntimeError("config corrupt")

    result = check_credentials(user_loader=_raises)
    assert result.status == WARN
    assert "config corrupt" in result.message


# ----------------------------- telemetry -------------------------------- #


def test_telemetry_off_when_disabled() -> None:
    result = check_telemetry({"MAPILIO_KIT_DISABLE_TELEMETRY": "1"})
    assert result.status == OK
    assert "disabled" in result.message.lower()


def test_telemetry_on_when_dsn_set() -> None:
    result = check_telemetry({"MAPILIO_KIT_SENTRY_DSN": "https://x@y/1"})
    assert result.details["dsn_configured"] is True


def test_telemetry_off_when_no_dsn() -> None:
    result = check_telemetry({})
    assert result.details["dsn_configured"] is False


# ------------------------------ report ---------------------------------- #


def test_report_overall_status_picks_worst() -> None:
    report = DoctorReport(checks=[
        CheckResult("a", OK, "fine"),
        CheckResult("b", WARN, "meh"),
    ])
    assert report.overall_status == WARN

    report.checks.append(CheckResult("c", FAIL, "bad"))
    assert report.overall_status == FAIL


def test_report_to_dict_round_trips_through_json() -> None:
    report = DoctorReport(checks=[CheckResult("a", OK, "fine", {"k": 1})])
    payload = json.dumps(report.to_dict())
    assert "fine" in payload
    assert "ok" in payload


def test_render_text_includes_each_check_name() -> None:
    report = DoctorReport(checks=[
        CheckResult("python", OK, "Python 3.11"),
        CheckResult("ffmpeg", WARN, "old"),
    ])
    text = render_text(report, use_color=False)
    assert "python" in text and "ffmpeg" in text
    assert "WARN" in text


def test_run_all_checks_returns_full_report(monkeypatch) -> None:
    # Force credential check to succeed without touching the real config file.
    import mapilio_kit.components.utilities.doctor as doctor_mod

    monkeypatch.setattr(
        "mapilio_kit.components.auth.login.list_all_users",
        lambda: [{"SettingsEmail": "x@y.z"}],
        raising=False,
    )
    # We don't actually care about ffmpeg/exiftool here — the check just
    # has to *run* (it'll be FAIL on this VM). The point is the aggregator.
    report = doctor_mod.run_all_checks("9.9.9")
    names = [c.name for c in report.checks]
    for expected in ("platform", "python", "mapilio_kit", "disk", "telemetry"):
        assert expected in names
