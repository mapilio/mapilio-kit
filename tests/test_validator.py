"""Unit tests for ``mapilio_kit.components.utilities.validator``.

The exif reading layer is replaced with a fake reader so tests don't depend
on a real EXIF parser or real image bytes on disk.
"""

from __future__ import annotations

import os

import pytest

from mapilio_kit.components.utilities.validator import (
    ImageRecord,
    Issue,
    _haversine_meters,
    _parse_exif_datetime,
    build_report,
    find_images,
    read_image_exif,
    validate_records,
)

# --------------------------- helpers / fixtures -------------------------- #


def _record(
    path: str,
    lat: float | None,
    lon: float | None,
    captured_at: float | None,
    error: str | None = None,
) -> ImageRecord:
    return ImageRecord(path=path, lat=lat, lon=lon, captured_at=captured_at, error=error)


# --------------------------- find_images -------------------------------- #


def test_find_images_returns_sorted_paths(tmp_path) -> None:
    (tmp_path / "b.jpg").write_bytes(b"")
    (tmp_path / "a.JPEG").write_bytes(b"")
    (tmp_path / "ignore.txt").write_bytes(b"")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.png").write_bytes(b"")

    out = find_images(str(tmp_path))
    assert [os.path.basename(p) for p in out] == ["a.JPEG", "b.jpg", "c.png"]


def test_find_images_skip_subfolders(tmp_path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.jpg").write_bytes(b"")

    out = find_images(str(tmp_path), skip_subfolders=True)
    assert [os.path.basename(p) for p in out] == ["a.jpg"]


def test_find_images_missing_dir_returns_empty(tmp_path) -> None:
    assert find_images(str(tmp_path / "does-not-exist")) == []


# --------------------------- exif parsing helpers ----------------------- #


def test_parse_exif_datetime_standard_format() -> None:
    ts = _parse_exif_datetime("2024:01:15 10:30:45")
    assert ts is not None
    assert ts > 1_700_000_000


def test_parse_exif_datetime_iso_with_microseconds() -> None:
    assert _parse_exif_datetime("2024-01-15T10:30:45.123") is not None


def test_parse_exif_datetime_garbage_returns_none() -> None:
    assert _parse_exif_datetime("not a date") is None


# --------------------------- haversine ---------------------------------- #


def test_haversine_zero_for_same_point() -> None:
    assert _haversine_meters((0.0, 0.0), (0.0, 0.0)) == pytest.approx(0.0, abs=1e-6)


def test_haversine_one_degree_lat_is_about_111km() -> None:
    d = _haversine_meters((0.0, 0.0), (1.0, 0.0))
    assert 110_000 < d < 112_000


# --------------------------- read_image_exif (mocked) ------------------- #


class _FakeRatio:
    def __init__(self, num, den=1):
        self.num = num
        self.den = den


class _FakeTag:
    def __init__(self, values):
        self.values = values

    def __str__(self) -> str:
        return str(self.values)


def test_read_image_exif_extracts_gps_and_time(tmp_path) -> None:
    p = tmp_path / "img.jpg"
    p.write_bytes(b"fake")

    def fake_reader(_fp):
        return {
            "GPS GPSLatitude": _FakeTag([_FakeRatio(40), _FakeRatio(42), _FakeRatio(0)]),
            "GPS GPSLatitudeRef": "N",
            "GPS GPSLongitude": _FakeTag([_FakeRatio(74), _FakeRatio(0), _FakeRatio(0)]),
            "GPS GPSLongitudeRef": "W",
            "EXIF DateTimeOriginal": "2024:01:15 10:30:45",
        }

    rec = read_image_exif(str(p), exif_reader=fake_reader)
    assert rec.lat == pytest.approx(40.7, abs=0.01)
    assert rec.lon == pytest.approx(-74.0, abs=0.01)
    assert rec.captured_at is not None


def test_read_image_exif_no_gps_returns_record_without_coords(tmp_path) -> None:
    p = tmp_path / "img.jpg"
    p.write_bytes(b"fake")

    def fake_reader(_fp):
        return {"EXIF DateTimeOriginal": "2024:01:15 10:30:45"}

    rec = read_image_exif(str(p), exif_reader=fake_reader)
    assert rec.lat is None and rec.lon is None
    assert rec.captured_at is not None


def test_read_image_exif_handles_missing_file() -> None:
    rec = read_image_exif("/nonexistent/path.jpg", exif_reader=lambda _fp: {})
    assert rec.error is not None
    assert "open failed" in rec.error


# --------------------------- validate_records --------------------------- #


def test_validate_flags_missing_gps() -> None:
    records = [_record("a.jpg", None, None, 100.0)]
    issues = validate_records(records)
    assert any(i.code == "missing_gps" for i in issues)


def test_validate_flags_invalid_gps() -> None:
    records = [_record("a.jpg", 200.0, 0.0, 100.0)]
    issues = validate_records(records)
    assert any(i.code == "invalid_gps" for i in issues)


def test_validate_warns_on_zero_zero_gps() -> None:
    records = [_record("a.jpg", 0.0, 0.0, 100.0)]
    issues = validate_records(records)
    assert any(i.code == "suspicious_gps_zero" for i in issues)


def test_validate_flags_missing_timestamp() -> None:
    records = [_record("a.jpg", 40.0, -74.0, None)]
    issues = validate_records(records)
    assert any(i.code == "missing_timestamp" for i in issues)


def test_validate_flags_duplicate_capture() -> None:
    records = [
        _record("a.jpg", 40.0, -74.0, 100.0),
        _record("b.jpg", 40.0, -74.0, 100.0),
    ]
    issues = validate_records(records)
    assert any(i.code == "duplicate_capture" for i in issues)


def test_validate_warns_on_large_gps_gap() -> None:
    records = [
        _record("a.jpg", 40.0, -74.0, 100.0),  # NYC
        _record("b.jpg", 34.0, -118.0, 200.0),  # LA — ~3900 km later
    ]
    issues = validate_records(records, max_gap_meters=10_000)
    assert any(i.code == "large_gps_gap" for i in issues)


def test_validate_warns_on_large_time_gap() -> None:
    records = [
        _record("a.jpg", 40.0, -74.0, 100.0),
        _record("b.jpg", 40.001, -74.001, 100.0 + 7200),  # +2h
    ]
    issues = validate_records(records, max_time_gap_seconds=3600)
    assert any(i.code == "large_time_gap" for i in issues)


def test_validate_clean_sequence_has_no_issues() -> None:
    records = [
        _record("a.jpg", 40.0, -74.0, 100.0),
        _record("b.jpg", 40.0001, -74.0001, 110.0),
        _record("c.jpg", 40.0002, -74.0002, 120.0),
    ]
    issues = validate_records(records)
    assert issues == []


def test_validate_handles_exif_read_error() -> None:
    records = [_record("bad.jpg", None, None, None, error="exif read failed: parse")]
    issues = validate_records(records)
    assert len(issues) == 1
    assert issues[0].code == "exif_read_error"
    assert issues[0].level == "error"


# ------------------------------ build_report ---------------------------- #


def test_build_report_counts_valid_images() -> None:
    records = [
        _record("a.jpg", 40.0, -74.0, 100.0),
        _record("b.jpg", None, None, 100.0),  # missing_gps
    ]
    issues = validate_records(records)
    report = build_report(records, issues)
    assert report.image_count == 2
    assert report.valid_count == 1
    assert report.has_errors


def test_build_report_summary_groups_codes() -> None:
    issues = [
        Issue(level="error", code="missing_gps", path="a", message=""),
        Issue(level="error", code="missing_gps", path="b", message=""),
        Issue(level="warning", code="duplicate_capture", path="c", message=""),
    ]
    report = build_report([], issues)
    assert report.summary == {"missing_gps": 2, "duplicate_capture": 1}
