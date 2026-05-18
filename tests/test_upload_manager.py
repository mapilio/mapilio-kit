"""Unit tests for UploadManager.upload() Content-Range header construction.

RFC 7233 §4.2 requires: Content-Range: bytes <start>-<end>/<total>
where <end> is the last byte index of the current chunk (0-indexed, inclusive),
NOT the total entity size.
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest

from mapilio_kit.components.upload.upload_manager import UploadManager

USER_ITEMS = {"SettingsEmail": "test@example.com"}


def _make_manager(entity_size: int) -> UploadManager:
    return UploadManager(
        user_access_token="test_token",
        session_key="test.zip",
        entity_size=entity_size,
    )


def _mock_get():
    """Stub for fetch_offset — returns 0 (fresh upload)."""
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"totalChunkUploaded": 0}
    return m


def _mock_post_json(hash_value: str = "abc123"):
    """Stub POST response that satisfies the finalization return path."""
    m = MagicMock()
    m.status_code = 200
    m.raise_for_status.return_value = None
    m.headers = {"content-type": "application/json"}
    m.text = f'{{"hash": "{hash_value}"}}'
    return m


@patch("mapilio_kit.components.upload.upload_manager.requests.post")
@patch("mapilio_kit.components.upload.upload_manager.requests.get")
def test_single_chunk_content_range(mock_get, mock_post):
    """Single chunk: Content-Range end must be last byte index, not total size."""
    total = 100
    mock_get.return_value = _mock_get()
    mock_post.return_value = _mock_post_json()

    manager = _make_manager(total)
    manager.upload(USER_ITEMS, io.BytesIO(b"x" * total))

    ranges = [
        call.kwargs["headers"]["content-range"]
        for call in mock_post.call_args_list
        if "content-range" in call.kwargs.get("headers", {})
    ]
    # First (data) chunk: bytes=0-99/100
    assert "bytes=0-99/100" in ranges, f"unexpected ranges: {ranges}"


@patch("mapilio_kit.components.upload.upload_manager.requests.post")
@patch("mapilio_kit.components.upload.upload_manager.requests.get")
def test_multi_chunk_content_range(mock_get, mock_post):
    """Multi-chunk upload: each chunk carries the correct byte range."""
    total = 150
    chunk_size = 100
    mock_get.return_value = _mock_get()
    mock_post.return_value = _mock_post_json()

    manager = _make_manager(total)
    manager.upload(USER_ITEMS, io.BytesIO(b"x" * total), chunk_size=chunk_size)

    ranges = [
        call.kwargs["headers"]["content-range"]
        for call in mock_post.call_args_list
        if "content-range" in call.kwargs.get("headers", {})
    ]
    assert "bytes=0-99/150" in ranges, f"unexpected ranges: {ranges}"
    assert "bytes=100-149/150" in ranges, f"unexpected ranges: {ranges}"
    # Verify the old wrong value (end == total) is NOT sent for data chunks
    assert "bytes=0-150/150" not in ranges, "old incorrect range still present"
