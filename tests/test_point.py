"""Tests for the geometry utilities in ``mapilio_kit.components.utilities.point``."""

from __future__ import annotations

import math

import pytest

from mapilio_kit.components.utilities.point import (
    Interpolator,
    Point,
    _interpolate_segment,
    calculate_ecef_from_lla,
    calculate_gps_distance,
    compute_bearing,
    determine_maximum_distance_from_start,
    extend_deduplicate_points,
    filter_points_by_distance,
    generate_pairs,
)

# ------------------------ basic distance / bearing ------------------------ #


def test_distance_zero_for_same_point() -> None:
    assert calculate_gps_distance((42.0, -11.0), (42.0, -11.0)) == pytest.approx(0.0, abs=1e-6)


def test_distance_doctest_example_within_expected_range() -> None:
    # Same example used in the function's doctest.
    d = calculate_gps_distance((42.1, -11.1), (42.2, -11.3))
    assert 19_000 < d < 20_000


def test_distance_is_symmetric() -> None:
    a, b = (40.7128, -74.0060), (34.0522, -118.2437)  # NYC <-> LA
    assert calculate_gps_distance(a, b) == pytest.approx(calculate_gps_distance(b, a), rel=1e-9)


def test_ecef_round_numbers_at_equator() -> None:
    # On the equator, lat=0, lon=0 → x=WGS84_a, y=0, z=0
    x, y, z = calculate_ecef_from_lla(0.0, 0.0)
    assert x == pytest.approx(6_378_137.0, rel=1e-9)
    assert y == pytest.approx(0.0, abs=1e-6)
    assert z == pytest.approx(0.0, abs=1e-6)


def test_compute_bearing_due_north_is_zero() -> None:
    bearing = compute_bearing(0.0, 0.0, 1.0, 0.0)
    assert bearing == pytest.approx(0.0, abs=1e-6)


def test_compute_bearing_due_east_is_90() -> None:
    bearing = compute_bearing(0.0, 0.0, 0.0, 1.0)
    assert bearing == pytest.approx(90.0, abs=1e-3)


def test_compute_bearing_due_south_is_180() -> None:
    bearing = compute_bearing(1.0, 0.0, 0.0, 0.0)
    assert bearing == pytest.approx(180.0, abs=1e-3)


def test_max_distance_from_start_zero_for_empty() -> None:
    assert determine_maximum_distance_from_start([]) == 0


def test_max_distance_from_start_handles_multiple() -> None:
    points = [(0.0, 0.0), (0.0, 0.0), (0.001, 0.001)]
    assert determine_maximum_distance_from_start(points) > 0


# ----------------------------- pair iterator ------------------------------ #


def test_generate_pairs_basic() -> None:
    assert list(generate_pairs([1, 2, 3, 4])) == [(1, 2), (2, 3), (3, 4)]


def test_generate_pairs_empty() -> None:
    assert list(generate_pairs([])) == []


def test_generate_pairs_single() -> None:
    assert list(generate_pairs([1])) == []


# --------------------------- interpolate segment -------------------------- #


def _pt(t: float, lat: float, lon: float, alt: float | None = 0.0) -> Point:
    return Point(time=t, lat=lat, lon=lon, alt=alt, angle=None)


def test_interpolate_midpoint() -> None:
    start = _pt(0.0, 0.0, 0.0, 0.0)
    end = _pt(10.0, 1.0, 1.0, 100.0)
    mid = _interpolate_segment(start, end, 5.0)
    assert mid.lat == pytest.approx(0.5)
    assert mid.lon == pytest.approx(0.5)
    assert mid.alt == pytest.approx(50.0)


def test_interpolate_handles_equal_times() -> None:
    start = _pt(0.0, 0.0, 0.0)
    end = _pt(0.0, 1.0, 1.0)
    out = _interpolate_segment(start, end, 0.0)
    # Weight degenerates to 0 → returns start coords.
    assert out.lat == pytest.approx(0.0)
    assert out.lon == pytest.approx(0.0)


def test_interpolate_alt_none_when_either_is_missing() -> None:
    start = _pt(0.0, 0.0, 0.0, alt=None)
    end = _pt(10.0, 1.0, 1.0, alt=100.0)
    out = _interpolate_segment(start, end, 5.0)
    assert out.alt is None


# ------------------------------ Interpolator ------------------------------ #


def test_interpolator_within_range() -> None:
    track = [_pt(0.0, 0.0, 0.0, 0.0), _pt(10.0, 1.0, 1.0, 100.0)]
    interp = Interpolator([track])
    out = interp.interpolate(5.0)
    assert out.lat == pytest.approx(0.5)
    assert out.lon == pytest.approx(0.5)


def test_interpolator_rejects_empty() -> None:
    with pytest.raises(ValueError):
        Interpolator([[]])


def test_interpolator_extrapolates_before_first_point() -> None:
    track = [_pt(10.0, 1.0, 1.0, 0.0), _pt(20.0, 2.0, 2.0, 0.0)]
    interp = Interpolator([track])
    # asking for t before track start: should still return a Point (extrapolated)
    out = interp.interpolate(5.0)
    assert isinstance(out, Point)


# --------------------- filter_points_by_distance / dedup ------------------ #


def test_filter_points_by_distance_drops_close_samples() -> None:
    samples = [
        _pt(0, 0.0, 0.0),
        _pt(1, 0.000001, 0.0),  # ~0.1m, way under 100m threshold
        _pt(2, 1.0, 1.0),  # very far, should be kept
    ]
    out = list(filter_points_by_distance(samples, min_distance=100.0, point_func=lambda p: p))
    assert len(out) == 2
    assert out[0].lat == 0.0
    assert out[1].lat == 1.0


def test_extend_deduplicate_points_skips_consecutive_duplicates() -> None:
    pts = [_pt(0, 1.0, 2.0), _pt(1, 1.0, 2.0), _pt(2, 1.5, 2.5), _pt(3, 1.5, 2.5)]
    out = extend_deduplicate_points(pts)
    assert [(p.lat, p.lon) for p in out] == [(1.0, 2.0), (1.5, 2.5)]


def test_extend_deduplicate_points_appends_to_existing() -> None:
    initial = [_pt(0, 1.0, 2.0)]
    out = extend_deduplicate_points([_pt(1, 1.0, 2.0), _pt(2, 3.0, 4.0)], to_extend=initial)
    assert out is initial  # mutated in place
    assert len(out) == 2
    assert (out[1].lat, out[1].lon) == (3.0, 4.0)
