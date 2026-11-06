"""Completion must return a usable handle or stop after one terminal POST."""

import io

import pytest
import requests

from mapilio_kit.components.upload import upload_manager, uploader

USER = {
    "SettingsEmail": "fixture@example.invalid",
    "SettingsUserKey": "fixture-user",
    "user_upload_token": "synthetic-token",
}


def _response(status, body=b"", content_type="application/json"):
    response = requests.Response()
    response.status_code = status
    response._content = body
    if content_type is not None:
        response.headers["content-type"] = content_type
    return response


INVALID_COMPLETIONS = [
    pytest.param(204, b"", "application/json", "204", id="no-content"),
    pytest.param(200, b"secret-response-body", "text/plain", "JSON", id="non-json"),
    pytest.param(200, b'{"hash":"opaque"}', None, "JSON", id="missing-content-type"),
    pytest.param(200, b'{"hash":"opaque"}', "application/json-invalid", "JSON", id="invalid-media-type"),
    pytest.param(200, b"secret-response-body", "application/json", "JSON", id="invalid-json"),
    pytest.param(200, b"null", "application/json", "object", id="null-json"),
    pytest.param(200, b"[]", "application/json", "object", id="array-json"),
    pytest.param(200, b'"secret-response-body"', "application/json", "object", id="string-json"),
    pytest.param(200, b"42", "application/json", "object", id="number-json"),
    pytest.param(200, b"true", "application/json", "object", id="boolean-json"),
    pytest.param(200, b"{}", "application/json", "hash", id="missing-hash"),
    pytest.param(200, b'{"hash":null}', "application/json", "hash", id="null-hash"),
    pytest.param(200, b'{"hash":""}', "application/json", "hash", id="empty-hash"),
    pytest.param(200, b'{"hash":123}', "application/json", "hash", id="number-hash"),
    pytest.param(200, b'{"hash":true}', "application/json", "hash", id="boolean-hash"),
    pytest.param(200, b'{"hash":[]}', "application/json", "hash", id="array-hash"),
    pytest.param(200, b'{"hash":{}}', "application/json", "hash", id="object-hash"),
]


class CompletionServer:
    def __init__(self, completion):
        self.completion = completion
        self.posts = []
        self.offsets = []
        self.stored = b""

    def get(self, url, headers):
        self.offsets.append(len(self.stored))
        return _response(200, b'{"totalChunkUploaded":0}')

    def post(self, url, headers, files):
        chunk = files["chunk"][1]
        self.posts.append((headers["content-range"], chunk))
        # Fail promptly against the original endless completion loop.
        assert sum(not sent for _, sent in self.posts) <= 1, "repeated terminal POST"
        if not chunk:
            return self.completion
        self.stored += chunk
        # Intermediate successful responses need no JSON completion payload.
        return _response(204, content_type=None)


def _connect(monkeypatch, server):
    delays = []
    monkeypatch.setattr(upload_manager.requests, "get", server.get)
    monkeypatch.setattr(upload_manager.requests, "post", server.post)
    monkeypatch.setattr(uploader.time, "sleep", delays.append)
    return delays


@pytest.mark.parametrize("status,body,content_type,reason", INVALID_COMPLETIONS)
@pytest.mark.parametrize("outer_retry", [False, True], ids=["manager", "retry-owner"])
def test_invalid_completion_stops_once_without_retry(
    monkeypatch, status, body, content_type, reason, outer_retry
):
    server = CompletionServer(_response(status, body, content_type))
    delays = _connect(monkeypatch, server)
    data = io.BytesIO(b"aabb")

    with pytest.raises(RuntimeError, match="Upload completion") as error:
        if outer_retry:
            uploader._upload_zipfile_fp(USER, data, 4, 2, session_key="fixture.zip")
        else:
            manager = upload_manager.UploadManager("synthetic-token", "fixture.zip", 4)
            manager.upload(USER, data, offset=0, chunk_size=2)

    assert reason in str(error.value)
    assert "secret-response-body" not in str(error.value)
    assert "synthetic-token" not in str(error.value)
    assert not uploader.is_retriable_exception(error.value)
    assert server.posts == [
        ("bytes=0-4/4", b"aa"),
        ("bytes=2-4/4", b"bb"),
        ("bytes=4-4/4", b""),
    ]
    assert server.stored == b"aabb"
    assert server.offsets == ([0] if outer_retry else [])
    assert delays == []


@pytest.mark.parametrize("content_type", ["application/json", "application/json; charset=utf-8"])
def test_valid_completion_preserves_hash_ranges_and_callbacks(monkeypatch, content_type):
    completion = _response(200, b'{"hash":" opaque-hash "}', content_type)
    server = CompletionServer(completion)
    _connect(monkeypatch, server)
    manager = upload_manager.UploadManager("synthetic-token", "fixture.zip", 4)
    callbacks = []
    manager.callbacks.append(lambda chunk, response: callbacks.append((chunk, response.status_code)))

    result = manager.upload(USER, io.BytesIO(b"aabb"), offset=0, chunk_size=2)

    assert result == " opaque-hash "
    assert callbacks == [(b"aa", 204), (b"bb", 204), (b"", 200)]
    assert server.posts == [
        ("bytes=0-4/4", b"aa"),
        ("bytes=2-4/4", b"bb"),
        ("bytes=4-4/4", b""),
    ]


def test_invalid_completion_prevents_metadata_upload(monkeypatch, tmp_path):
    image = tmp_path / "fixture.jpg"
    image.write_bytes(b"synthetic-image")
    desc = {
        "path": str(tmp_path),
        "filename": image.name,
        "heading": 0,
        "latitude": 0,
        "longitude": 0,
        "captureTime": "2026-11-06T00:00:00Z",
        "sequenceUuid": "fixture-sequence",
    }
    server = CompletionServer(_response(200, b"{}"))
    delays = _connect(monkeypatch, server)
    metadata_requests = []

    def zip_sequence(image_dir, sequences, fp, tqdm_desc):
        # EXIF processing is unrelated; keep all upload orchestration real.
        fp.write(b"aabb")
        return "fixture-md5"

    monkeypatch.setattr(uploader, "_zip_sequence", zip_sequence)
    monkeypatch.setattr(uploader.requests, "request", lambda *a, **kw: metadata_requests.append(kw))

    with pytest.raises(RuntimeError, match="Upload completion.*hash"):
        uploader.upload_image_dir_and_description(str(tmp_path), [desc], USER)

    assert metadata_requests == []
    assert server.posts == [("bytes=0-4/4", b"aabb"), ("bytes=4-4/4", b"")]
    assert server.offsets == [0]
    assert delays == []
