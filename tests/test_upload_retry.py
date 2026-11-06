"""HTTP failures must reach the existing resumable-upload retry owner."""

import io
import json
import re

import pytest
import requests

from mapilio_kit.components.upload import upload_manager, uploader

USER = {"SettingsEmail": "fixture@example.invalid", "user_upload_token": "synthetic-token"}


def _response(status, body):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.headers["content-type"] = "application/json"
    response.url = "https://upload.example.invalid/upload"
    response.request = requests.Request("POST", response.url).prepare()
    return response


class UploadServer:
    def __init__(self, status=500, persist_failed=False, always_fail=False):
        self.status = status
        self.persist_failed = persist_failed
        self.always_fail = always_fail
        self.failed = False
        self.stored = b""
        self.posts = []
        self.offsets = []

    def get(self, url, headers):
        self.offsets.append(len(self.stored))
        return _response(200, {"totalChunkUploaded": len(self.stored)})

    def post(self, url, headers, files):
        chunk = files["chunk"][1]
        self.posts.append((headers["content-range"], chunk))
        # Bound the unfixed client's tight loop so the regression fails promptly.
        assert len(self.posts) <= (205 if self.always_fail else 20), "unbounded upload loop"
        start, end, total = map(int, re.fullmatch(r"bytes=(\d+)-(\d+)/(\d+)", headers["content-range"]).groups())
        if self.always_fail or (not self.failed and len(self.stored) == 2):
            self.failed = True
            if self.persist_failed:
                self.stored += chunk
            return _response(self.status, {"message": "upload failed"})
        if not chunk and start == end == total == len(self.stored):
            return _response(200, {"hash": "fixture-hash"})
        if start != len(self.stored) or start >= end:
            return _response(400, {"message": "Bad chunk provided"})
        self.stored += chunk
        return _response(200, {})


def _connect(monkeypatch, server):
    delays = []
    monkeypatch.setattr(upload_manager.requests, "get", server.get)
    monkeypatch.setattr(upload_manager.requests, "post", server.post)
    monkeypatch.setattr(uploader.time, "sleep", delays.append)
    return delays


@pytest.mark.parametrize("persist_failed", [False, True], ids=["chunk-not-stored", "chunk-already-stored"])
def test_http_500_refetches_offset_and_resumes_exact_bytes(monkeypatch, persist_failed):
    server = UploadServer(persist_failed=persist_failed)
    delays = _connect(monkeypatch, server)

    result = uploader._upload_zipfile_fp(USER, io.BytesIO(b"aabbccdd"), 8, 2, session_key="fixture.zip")

    assert result == "fixture-hash"
    assert server.stored == b"aabbccdd"
    assert server.offsets == [0, 4 if persist_failed else 2]
    assert delays == [2]
    assert server.posts == [
        ("bytes=0-8/8", b"aa"),
        ("bytes=2-8/8", b"bb"),
        *([] if persist_failed else [("bytes=2-8/8", b"bb")]),
        ("bytes=4-8/8", b"cc"),
        ("bytes=6-8/8", b"dd"),
        ("bytes=8-8/8", b""),
    ]


@pytest.mark.parametrize("status", [400, 401, 403])
def test_ordinary_http_4xx_stops_without_retry(monkeypatch, status):
    server = UploadServer(status=status, always_fail=True)
    delays = _connect(monkeypatch, server)

    with pytest.raises(requests.HTTPError) as error:
        uploader._upload_zipfile_fp(USER, io.BytesIO(b"aabb"), 4, 2, session_key="fixture.zip")

    assert error.value.__cause__.response.status_code == status
    assert server.posts == [("bytes=0-4/4", b"aa")]
    assert server.offsets == [0]
    assert server.stored == b""
    assert delays == []


def test_permanent_http_500_exhausts_bounded_retry_with_backoff(monkeypatch):
    server = UploadServer(always_fail=True)
    delays = _connect(monkeypatch, server)

    with pytest.raises(requests.HTTPError) as error:
        uploader._upload_zipfile_fp(USER, io.BytesIO(b"aabb"), 4, 2, session_key="fixture.zip")

    assert error.value.__cause__.response.status_code == 500
    assert len(server.posts) == 201
    assert server.posts == [("bytes=0-4/4", b"aa")] * 201
    assert server.offsets == [0] * 201
    assert server.stored == b""
    assert delays == [2, 4, 8] + [16] * 197
