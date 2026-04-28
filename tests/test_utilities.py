"""Tests for ``mapilio_kit.components.utilities.utilities``.

These exercise pure helpers that don't require ffmpeg/exiftool/sentry to be
installed on the host running the tests.
"""

from __future__ import annotations

import hashlib
import io

import pytest

from mapilio_kit.components.utilities.utilities import (
    DEFAULT_CHUNK_FRAMES,
    LARGE_VIDEO_CHUNK_FRAMES,
    calculate_aspect_ratio,
    calculate_chunk_size,
    calculation_vfov,
    find_fov2,
    is_large_video,
    md5sum_fp,
    photo_uuid_generate,
)

# ------------------------------ aspect ratios ----------------------------- #


@pytest.mark.parametrize(
    "size, expected",
    [
        ("1920x1080", "16:9"),
        ("1280x720", "16:9"),
        ("4000x3000", "4:3"),
        ("1024x1024", "1:1"),
        ("3840x2160", "16:9"),
    ],
)
def test_calculate_aspect_ratio(size: str, expected: str) -> None:
    assert calculate_aspect_ratio(size) == expected


# --------------------------------- vFOV ----------------------------------- #


def test_calculation_vfov_known_value() -> None:
    # 118.2° hFOV at 16:9 → vFOV ≈ 86.45° using the project's formula
    # (2·atan(tan(hfov/2) / (16/9))).
    vfov = calculation_vfov(118.2, ("16", "9"))
    assert vfov == pytest.approx(86.45, abs=0.05)


def test_calculation_vfov_square_ratio() -> None:
    vfov = calculation_vfov(90.0, ("1", "1"))
    assert vfov == pytest.approx(90.0, abs=1e-2)


# ---------------------------- find_fov2 lookup ---------------------------- #


def test_find_fov2_lookup_known_pair() -> None:
    # ('hero7', 'wide', '4:3') is in the rules table.
    out = find_fov2("hero7", "wide", "4:3")
    assert out == [122.6, 94.4]


def test_find_fov2_unknown_raises() -> None:
    with pytest.raises(KeyError):
        find_fov2("nonexistent_camera", "weird", "1:1")


# ---------------------------- video size helpers -------------------------- #


def test_is_large_video_true_above_threshold() -> None:
    assert is_large_video(2 * 1024 * 1024 * 1024) is True


def test_is_large_video_false_below_threshold() -> None:
    assert is_large_video(100 * 1024 * 1024) is False


def test_is_large_video_custom_threshold() -> None:
    assert is_large_video(10, large_video_threshold=5) is True
    assert is_large_video(3, large_video_threshold=5) is False


# ---------------------------- chunk size logic --------------------------- #
# Regression test for the UnboundLocalError that used to happen when
# calculate_chunk_size was called with video_size <= threshold.


def test_calculate_chunk_size_small_video_returns_default() -> None:
    chunk = calculate_chunk_size(100 * 1024 * 1024)  # 100 MB → not large
    assert chunk == DEFAULT_CHUNK_FRAMES
    assert chunk > 0


def test_calculate_chunk_size_large_video_returns_smaller_chunks() -> None:
    chunk = calculate_chunk_size(2 * 1024 * 1024 * 1024)  # 2 GB → large
    assert chunk == LARGE_VIDEO_CHUNK_FRAMES
    assert chunk < DEFAULT_CHUNK_FRAMES


def test_calculate_chunk_size_at_exact_threshold_uses_default() -> None:
    # ``> threshold`` means equality should fall into the "small" branch.
    threshold = 5
    assert calculate_chunk_size(threshold, large_video_threshold=threshold) == DEFAULT_CHUNK_FRAMES


def test_calculate_chunk_size_above_custom_threshold() -> None:
    assert calculate_chunk_size(10, large_video_threshold=5) == LARGE_VIDEO_CHUNK_FRAMES


# ----------------------------- md5 streaming ------------------------------ #


def test_md5sum_fp_matches_hashlib() -> None:
    payload = b"mapilio-kit-test-payload" * 1024
    expected = hashlib.md5(payload).hexdigest()
    fp = io.BytesIO(payload)
    digest = md5sum_fp(fp).hexdigest()
    assert digest == expected


def test_md5sum_fp_accepts_existing_hash_object() -> None:
    fp = io.BytesIO(b"hello world")
    h = hashlib.md5()
    h.update(b"prefix:")
    out = md5sum_fp(fp, md5=h).hexdigest()
    assert out == hashlib.md5(b"prefix:hello world").hexdigest()


# ---------------------------- photo_uuid_generate ------------------------- #


def test_photo_uuid_generate_adds_uuid_to_all_but_last() -> None:
    descs = [
        {"captureTime": "2024-01-01T00:00:00Z"},
        {"captureTime": "2024-01-01T00:00:01Z"},
        {"captureTime": "tail"},  # function explicitly skips the last item
    ]
    out = photo_uuid_generate("user@example.com", descs)
    assert "photoUuid" in out[0]
    assert "photoUuid" in out[1]
    assert "photoUuid" not in out[2]


def test_photo_uuid_generate_produces_stable_hash() -> None:
    descs = [{"captureTime": "2024-01-01T00:00:00Z"}, {"captureTime": "tail"}]
    expected = hashlib.md5(b"user@example.com--2024-01-01T00:00:00Z").hexdigest()
    out = photo_uuid_generate("user@example.com", descs)
    assert out[0]["photoUuid"] == expected
