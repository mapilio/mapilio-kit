"""The chunked upload must keep to the upload server's own range format.

``FakeUploadServer`` models the server's rules: a chunk must have start < end and start at
the stored offset, and an empty request with start == end == total completes the upload.
"""

import io
import re

import pytest
import requests

from mapilio_kit.components.upload import upload_manager
from mapilio_kit.components.upload.upload_manager import UploadManager

USER = {"SettingsEmail": "fixture@example.invalid"}
CHUNK_SIZE = 100
MAX_REQUESTS = 20  # upload() retries in a loop, so a broken client must not hang the suite


def _response(status, body=b""):
    response = requests.Response()
    response.status_code = status
    response._content = body
    response.headers["content-type"] = "application/json"
    return response


class FakeUploadServer:
    def __init__(self, already_stored=b""):
        self.stored = already_stored
        self.ranges = []

    def post(self, url, headers, files):
        range_header = headers["content-range"]
        self.ranges.append(range_header)
        assert len(self.ranges) <= MAX_REQUESTS, f"upload did not finish: {self.ranges}"

        chunk = files["chunk"][1]
        match = re.fullmatch(r"bytes=(\d+)-(\d+)/(\d+)", range_header)
        start, end, total = map(int, match.groups())

        if not chunk and start == end == total == len(self.stored):
            return _response(200, b'{"hash": "opaque-hash"}')
        if start >= end or start != len(self.stored):
            return _response(400, b'{"error": "invalid range"}')

        self.stored += chunk
        return _response(200, b"{}")


def _payload(size):
    return bytes(i % 251 for i in range(size))


@pytest.mark.parametrize(
    ("size", "offset", "expected_ranges"),
    [
        pytest.param(1, 0, ["bytes=0-1/1", "bytes=1-1/1"], id="one-byte-file"),
        pytest.param(100, 0, ["bytes=0-100/100", "bytes=100-100/100"], id="exactly-one-chunk"),
        pytest.param(
            200,
            0,
            ["bytes=0-200/200", "bytes=100-200/200", "bytes=200-200/200"],
            id="exact-multiple-of-chunks",
        ),
        pytest.param(
            101,
            0,
            ["bytes=0-101/101", "bytes=100-101/101", "bytes=101-101/101"],
            id="final-remainder",
        ),
        pytest.param(
            250,
            100,
            ["bytes=100-250/250", "bytes=200-250/250", "bytes=250-250/250"],
            id="resumed-mid-file",
        ),
        pytest.param(101, 100, ["bytes=100-101/101", "bytes=101-101/101"], id="resumed-final-byte"),
    ],
)
def test_transfer_follows_server_range_format(monkeypatch, size, offset, expected_ranges):
    payload = _payload(size)
    server = FakeUploadServer(already_stored=payload[:offset])
    monkeypatch.setattr(upload_manager.requests, "post", server.post)

    manager = UploadManager("synthetic-token", "session-key", size)
    file_hash = manager.upload(USER, io.BytesIO(payload), offset=offset, chunk_size=CHUNK_SIZE)

    assert server.ranges == expected_ranges
    assert server.stored == payload
    assert file_hash == "opaque-hash"


@pytest.mark.parametrize("status", [400, 500])
@pytest.mark.parametrize("successful_chunks", [0, 1])
def test_http_error_stops_before_reading_another_chunk(monkeypatch, status, successful_chunks):
    sent = []
    confirmed = []

    def post(url, headers, files):
        sent.append((headers["content-range"], files["chunk"][1]))
        assert len(sent) <= successful_chunks + 1, "continued after the failed chunk"
        if len(sent) <= successful_chunks:
            return _response(200, b"{}")
        return _response(status, b'{"message": "upload failed"}')

    monkeypatch.setattr(upload_manager.requests, "post", post)
    manager = UploadManager("synthetic-token", "session-key", 4)
    manager.callbacks.append(lambda chunk, response: confirmed.append(chunk))
    data = io.BytesIO(b"aabb")

    with pytest.raises(requests.HTTPError) as error:
        manager.upload(USER, data, offset=0, chunk_size=2)

    assert error.value.response.status_code == status
    assert sent == [("bytes=0-4/4", b"aa"), ("bytes=2-4/4", b"bb")][:successful_chunks + 1]
    assert confirmed == [b"aa"][:successful_chunks]
    assert data.tell() == (successful_chunks + 1) * 2
